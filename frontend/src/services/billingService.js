/**
 * Google Digital Goods API Service for PWA Billing
 * Handles subscription purchases through Google Play Store
 */

// Product IDs - Configure these in Google Play Console
export const PRODUCT_IDS = {
  PREMIUM_MONTHLY: 'premium_monthly_1999', // €19.99/month
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
    console.log('[Billing] Digital Goods API not available');
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
 */
export const getProductDetails = async (productIds = [PRODUCT_IDS.PREMIUM_MONTHLY]) => {
  const service = await getDigitalGoodsService();
  if (!service) {
    // Return mock data for development/testing
    return [{
      itemId: PRODUCT_IDS.PREMIUM_MONTHLY,
      title: 'Fat & Slim Premium',
      description: 'Abonnement mensuel Premium avec IA illimitée, recettes exclusives et plus',
      price: {
        currency: 'EUR',
        value: '19.99',
      },
      subscriptionPeriod: 'P1M', // 1 month
    }];
  }

  try {
    const details = await service.getDetails(productIds);
    console.log('[Billing] Product details:', details);
    return details;
  } catch (error) {
    console.error('[Billing] Failed to get product details:', error);
    return [];
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
 */
export const purchaseSubscription = async (productId = PRODUCT_IDS.PREMIUM_MONTHLY) => {
  // Check if Payment Request API is available
  if (!('PaymentRequest' in window)) {
    throw new Error('Payment Request API not supported');
  }

  // Get product details first
  const products = await getProductDetails([productId]);
  const product = products.find(p => p.itemId === productId);
  
  if (!product) {
    throw new Error('Product not found');
  }

  // Create payment method data for Google Play Billing
  const paymentMethodData = [{
    supportedMethods: PLAY_BILLING_URL,
    data: {
      sku: productId,
    },
  }];

  // Payment details
  const paymentDetails = {
    total: {
      label: product.title,
      amount: {
        currency: product.price?.currency || 'EUR',
        value: product.price?.value || '19.99',
      },
    },
  };

  try {
    const request = new PaymentRequest(paymentMethodData, paymentDetails);
    
    // Check if can make payment
    const canMakePayment = await request.canMakePayment();
    if (!canMakePayment) {
      throw new Error('Cannot make payment through Google Play');
    }

    // Show payment UI
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
      return { success: false, error: 'Payment cancelled by user' };
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
