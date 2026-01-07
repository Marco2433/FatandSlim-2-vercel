import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import {
  isDigitalGoodsAvailable,
  getProductDetails,
  checkExistingPurchases,
  purchaseSubscription,
  PRODUCT_IDS,
} from '../services/billingService';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PremiumContext = createContext(null);

export const usePremium = () => {
  const context = useContext(PremiumContext);
  if (!context) {
    throw new Error('usePremium must be used within PremiumProvider');
  }
  return context;
};

export const PremiumProvider = ({ children }) => {
  const { user } = useAuth();
  const [isPremium, setIsPremium] = useState(false);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);
  const [productInfo, setProductInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [priceLoading, setPriceLoading] = useState(true);
  const [billingAvailable, setBillingAvailable] = useState(false);

  // Premium features list
  const premiumFeatures = [
    {
      id: 'unlimited_ai',
      title: 'IA Illimitée',
      description: 'Générez autant de plans repas et conseils IA que vous voulez',
      icon: '🤖',
    },
    {
      id: 'exclusive_recipes',
      title: 'Recettes Exclusives',
      description: 'Accédez à plus de 500 recettes premium et bariatriques avancées',
      icon: '👨‍🍳',
    },
    {
      id: 'premium_workouts',
      title: 'Programmes Premium',
      description: 'Programmes d\'entraînement personnalisés par des coachs certifiés',
      icon: '💪',
    },
    {
      id: 'priority_support',
      title: 'Support Prioritaire',
      description: 'Assistance prioritaire et réponses sous 24h',
      icon: '⭐',
    },
    {
      id: 'advanced_analytics',
      title: 'Statistiques Avancées',
      description: 'Analyses détaillées de votre progression et prédictions',
      icon: '📊',
    },
    {
      id: 'no_ads',
      title: 'Sans Publicités',
      description: 'Profitez d\'une expérience 100% sans publicités',
      icon: '🚫',
    },
  ];

  // Check if billing is available
  useEffect(() => {
    const available = isDigitalGoodsAvailable();
    setBillingAvailable(available);
    console.log('[Premium] Google Play Billing available:', available);
  }, []);

  // Load product info from Google Play (NOT hardcoded)
  useEffect(() => {
    const loadProductInfo = async () => {
      setPriceLoading(true);
      try {
        // This fetches real pricing from Google Play
        const products = await getProductDetails();
        
        if (products && products.length > 0) {
          setProductInfo(products[0]);
          console.log('[Premium] Product info from Google:', products[0]);
        } else {
          // No price available - user not on Play Store version
          setProductInfo(null);
          console.log('[Premium] No product info available - app not from Play Store');
        }
      } catch (error) {
        console.error('[Premium] Failed to load product info:', error);
        setProductInfo(null);
      } finally {
        setPriceLoading(false);
      }
    };
    
    loadProductInfo();
  }, [billingAvailable]);

  // Check premium status from backend
  const checkPremiumStatus = useCallback(async () => {
    if (!user) {
      setIsPremium(false);
      setSubscriptionDetails(null);
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/premium/status`, {
        withCredentials: true,
      });
      
      setIsPremium(response.data.is_premium);
      setSubscriptionDetails(response.data.subscription);
    } catch (error) {
      console.error('Failed to check premium status:', error);
      setIsPremium(false);
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Check for existing purchases on mount
  useEffect(() => {
    const syncPurchases = async () => {
      if (!user || !billingAvailable) {
        setLoading(false);
        return;
      }

      try {
        // Check existing purchases from Google Play
        const purchases = await checkExistingPurchases();
        
        if (purchases.length > 0) {
          // Sync with backend
          for (const purchase of purchases) {
            await axios.post(`${API}/premium/verify`, {
              purchase_token: purchase.purchaseToken,
              product_id: purchase.itemId,
            }, { withCredentials: true });
          }
        }
      } catch (error) {
        console.error('Failed to sync purchases:', error);
      }

      // Check status from backend
      await checkPremiumStatus();
    };

    syncPurchases();
  }, [user, billingAvailable, checkPremiumStatus]);

  // Purchase premium subscription
  const purchasePremium = async () => {
    if (!user) {
      throw new Error('Vous devez être connecté pour vous abonner');
    }

    if (!billingAvailable) {
      throw new Error('L\'achat in-app n\'est disponible que via l\'application Google Play Store');
    }

    try {
      const result = await purchaseSubscription(PRODUCT_IDS.PREMIUM_MONTHLY);
      
      if (result.success) {
        // Verify purchase with backend
        await axios.post(`${API}/premium/verify`, {
          purchase_token: result.purchaseToken,
          product_id: result.productId,
        }, { withCredentials: true });

        // Refresh status
        await checkPremiumStatus();
        
        return { success: true };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error('Purchase failed:', error);
      return { success: false, error: error.message };
    }
  };

  // Cancel subscription (redirect to Play Store subscriptions)
  const cancelSubscription = () => {
    // Open Play Store subscription management
    window.open('https://play.google.com/store/account/subscriptions', '_blank');
  };

  // Check if a feature requires premium
  const requiresPremium = (featureId) => {
    return premiumFeatures.some(f => f.id === featureId);
  };

  // Check if user can access a premium feature
  const canAccessFeature = (featureId) => {
    if (!requiresPremium(featureId)) return true;
    return isPremium;
  };

  // Get formatted price from Google (or null if not available)
  // IMPORTANT: Use formattedPrice directly from Google Play
  // It's already properly formatted with locale, currency symbol, decimals
  const getFormattedPrice = () => {
    if (!productInfo) {
      return null;
    }
    // Use formattedPrice directly - Google provides it properly formatted
    // e.g., "23,99 €" or "$23.99" depending on user's locale
    return productInfo.formattedPrice || null;
  };

  return (
    <PremiumContext.Provider value={{
      isPremium,
      loading,
      priceLoading,
      subscriptionDetails,
      productInfo,
      premiumFeatures,
      billingAvailable,
      purchasePremium,
      cancelSubscription,
      checkPremiumStatus,
      requiresPremium,
      canAccessFeature,
      getFormattedPrice,
    }}>
      {children}
    </PremiumContext.Provider>
  );
};

export default PremiumContext;
