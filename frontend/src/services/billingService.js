/**
 * Google Digital Goods API Service for PWA Billing
 * Handles subscription purchases through Google Play Store
 * 
 * IMPORTANT: Prices are ALWAYS fetched from Google Play, never hardcoded
 * Google handles: currencies, taxes (VAT), regional pricing, compliance
 */

// Product IDs - Configure these in Google Play Console
export const PRODUCT_IDS = {
  PREMIUM_MONTHLY: 'premium_monthly_1999', // ID only, price comes from Google
};

// Google Play Billing service URL
const PLAY_BILLING_URL = 'https://play.google.com/billing';

/**
 * Check if Digital Goods API is available
 * Only available when app is installed from Play Store as TWA
 */
export const isDigitalGoodsAvailable = () => {
  return 'getDigitalGoodsService' in window;
};

/**
 * Get the Digital Goods Service instance
 */
export const getDigitalGoodsService = async () => {
  if (!isDigitalGoodsAvailable()) {
    console.log('[Billing] Digital Goods API not available - app not installed from Play Store');
    return null;
  }

  try {
    const service = await window.getDigitalGoodsService(PLAY_BILLING_URL);
    console.log('[Billing] Digital Goods Service connected');
    return service;
  } catch (error) {
    console.error('[Billing] Failed to get Digital Goods Service:', error);
    return null;
  }
};

/**
 * Get product details from Google Play
 * Returns pricing info with correct currency, taxes, and regional pricing
 * 
 * Google Play Digital Goods API returns:
 * - itemId: string
 * - title: string  
 * - description: string
 * - price: { value: string, currency: string } OR just the formatted string
 * - formattedPrice: string (e.g., "23,99 €") - THIS IS WHAT WE SHOULD DISPLAY
 * - subscriptionPeriod: string (e.g., "P1M")
 */
export const getProductDetails = async (productIds = [PRODUCT_IDS.PREMIUM_MONTHLY]) => {
  const service = await getDigitalGoodsService();
  
  if (!service) {
    // Return null when not available - UI should handle this case
    console.log('[Billing] Cannot fetch prices - Digital Goods API not available');
    return null;
  }

  try {
    const details = await service.getDetails(productIds);
    console.log('[Billing] Raw product details from Google:', JSON.stringify(details));
    
    // Use formattedPrice directly from Google - it's already properly formatted
    // with correct locale, currency symbol, and decimal places
    return details.map(item => {
      // Log for debugging
      console.log('[Billing] Item formattedPrice:', item.formattedPrice);
      console.log('[Billing] Item price object:', item.price);
      
      return {
        itemId: item.itemId,
        title: item.title,
        description: item.description,
        // IMPORTANT: Use formattedPrice from Google directly
        // This is already formatted correctly (e.g., "23,99 €")
        formattedPrice: item.formattedPrice,
        // Keep raw price for any calculations if needed
        price: item.price,
        subscriptionPeriod: item.subscriptionPeriod,
      };
    });
  } catch (error) {
    console.error('[Billing] Failed to get product details from Google:', error);
    return null;
  }
};

/**
 * Check existing purchases/entitlements
 */
export const checkExistingPurchases = async () => {
  const service = await getDigitalGoodsService();
  if (!service) {
    return [];
  }

  try {
    const purchases = await service.listPurchases();
    console.log('[Billing] Existing purchases:', purchases);
    return purchases;
  } catch (error) {
    console.error('[Billing] Failed to check purchases:', error);
    return [];
  }
};

/**
 * Initiate a purchase using Payment Request API
 * Price is determined by Google Play, not by the app
 */
export const purchaseSubscription = async (productId = PRODUCT_IDS.PREMIUM_MONTHLY) => {
  // Check if Payment Request API is available
  if (!('PaymentRequest' in window)) {
    throw new Error('Payment Request API not supported');
  }

  // Get product details from Google first
  const products = await getProductDetails([productId]);
  
  if (!products || products.length === 0) {
    throw new Error('Impossible de récupérer les informations du produit depuis Google Play');
  }
  
  const product = products.find(p => p.itemId === productId);
  
  if (!product) {
    throw new Error('Produit non trouvé dans Google Play');
  }

  // Create payment method data for Google Play Billing
  const paymentMethodData = [{
    supportedMethods: PLAY_BILLING_URL,
    data: {
      sku: productId,
    },
  }];

  // Payment details - Google provides the actual price
  const paymentDetails = {
    total: {
      label: product.title,
      amount: {
        currency: product.price.currency,
        value: product.price.value,
      },
    },
  };

  try {
    const request = new PaymentRequest(paymentMethodData, paymentDetails);
    
    // Check if can make payment
    const canMakePayment = await request.canMakePayment();
    if (!canMakePayment) {
      throw new Error('Paiement non disponible via Google Play');
    }

    // Show payment UI (Google handles the actual payment)
    const paymentResponse = await request.show();
    
    // Get purchase token from response
    const { purchaseToken } = paymentResponse.details;
    
    // Complete the payment
    await paymentResponse.complete('success');
    
    console.log('[Billing] Purchase successful, token:', purchaseToken);
    
    return {
      success: true,
      purchaseToken,
      productId,
    };
  } catch (error) {
    console.error('[Billing] Purchase failed:', error);
    
    if (error.name === 'AbortError') {
      return { success: false, error: 'Paiement annulé' };
    }
    
    return { success: false, error: error.message };
  }
};

/**
 * Acknowledge a purchase (required by Google Play)
 */
export const acknowledgePurchase = async (purchaseToken) => {
  const service = await getDigitalGoodsService();
  if (!service) {
    return false;
  }

  try {
    await service.acknowledge(purchaseToken, 'onetime');
    console.log('[Billing] Purchase acknowledged');
    return true;
  } catch (error) {
    console.error('[Billing] Failed to acknowledge purchase:', error);
    return false;
  }
};

/**
 * Consume a purchase (for consumables, not subscriptions)
 */
export const consumePurchase = async (purchaseToken) => {
  const service = await getDigitalGoodsService();
  if (!service) {
    return false;
  }

  try {
    await service.consume(purchaseToken);
    console.log('[Billing] Purchase consumed');
    return true;
  } catch (error) {
    console.error('[Billing] Failed to consume purchase:', error);
    return false;
  }
};

export default {
  isDigitalGoodsAvailable,
  getDigitalGoodsService,
  getProductDetails,
  checkExistingPurchases,
  purchaseSubscription,
  acknowledgePurchase,
  consumePurchase,
  PRODUCT_IDS,
};
