import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePremium } from '@/context/PremiumContext';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Check, 
  Crown, 
  Sparkles, 
  Shield,
  Zap,
  Star,
  Loader2,
  ExternalLink
} from 'lucide-react';

export default function PremiumPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { 
    isPremium, 
    loading, 
    subscriptionDetails,
    productInfo,
    premiumFeatures,
    billingAvailable,
    purchasePremium,
    cancelSubscription,
  } = usePremium();
  
  const [purchasing, setPurchasing] = useState(false);

  const handlePurchase = async () => {
    if (!user) {
      toast.error('Vous devez être connecté pour vous abonner');
      navigate('/login');
      return;
    }

    setPurchasing(true);
    try {
      const result = await purchasePremium();
      
      if (result.success) {
        toast.success('🎉 Bienvenue dans Fat & Slim Premium !');
      } else {
        if (result.error !== 'Payment cancelled by user') {
          toast.error(result.error || 'Erreur lors de l\'achat');
        }
      }
    } catch (error) {
      toast.error('Erreur lors de l\'achat');
    } finally {
      setPurchasing(false);
    }
  };

  const handleCancel = () => {
    cancelSubscription();
    toast.info('Redirection vers Google Play pour gérer votre abonnement');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Already premium - show status
  if (isPremium) {
    return (
      <div className="min-h-screen bg-background pb-20">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-lg border-b">
          <div className="flex items-center justify-between p-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="font-heading text-lg font-semibold">Mon Abonnement</h1>
            <div className="w-10" />
          </div>
        </div>

        <div className="p-4 space-y-6">
          {/* Premium Status Card */}
          <Card className="overflow-hidden border-2 border-yellow-500/50 bg-gradient-to-br from-yellow-500/10 to-orange-500/10">
            <CardContent className="p-6 text-center">
              <img 
                src="/premium-badge.png" 
                alt="Premium" 
                className="w-32 h-32 mx-auto mb-4 object-contain"
              />
              <h2 className="text-2xl font-bold text-yellow-500 mb-2">
                Vous êtes Premium !
              </h2>
              <p className="text-muted-foreground mb-4">
                Profitez de tous les avantages exclusifs
              </p>
              
              {subscriptionDetails && (
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Abonnement actif depuis: {new Date(subscriptionDetails.start_date).toLocaleDateString('fr-FR')}</p>
                  <p>Prochain renouvellement: {new Date(subscriptionDetails.next_billing_date).toLocaleDateString('fr-FR')}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Features List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                Vos avantages Premium
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {premiumFeatures.map((feature) => (
                <div key={feature.id} className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-lg">{feature.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-medium flex items-center gap-2">
                      {feature.title}
                      <Check className="w-4 h-4 text-green-500" />
                    </h4>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Manage Subscription */}
          <Button 
            variant="outline" 
            className="w-full"
            onClick={handleCancel}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Gérer mon abonnement
          </Button>
        </div>
      </div>
    );
  }

  // Not premium - show upgrade page
  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-lg border-b">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="font-heading text-lg font-semibold">Passer Premium</h1>
          <div className="w-10" />
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Hero Section */}
        <div className="text-center py-6">
          <img 
            src="/premium-badge.png" 
            alt="Premium" 
            className="w-40 h-40 mx-auto mb-4 object-contain drop-shadow-2xl"
          />
          <h2 className="text-3xl font-bold mb-2">
            <span className="bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              Fat & Slim Premium
            </span>
          </h2>
          <p className="text-muted-foreground max-w-sm mx-auto">
            Débloquez tout le potentiel de votre transformation avec nos fonctionnalités exclusives
          </p>
        </div>

        {/* Price Card */}
        <Card className="overflow-hidden border-2 border-yellow-500/50 relative">
          <div className="absolute top-0 right-0">
            <Badge className="rounded-none rounded-bl-lg bg-yellow-500 text-black">
              POPULAIRE
            </Badge>
          </div>
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-lg">Abonnement Mensuel</CardTitle>
            <div className="mt-4">
              <span className="text-4xl font-bold">19,99€</span>
              <span className="text-muted-foreground">/mois</span>
            </div>
            <CardDescription>
              Renouvelé automatiquement chaque mois
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <Button 
              className="w-full h-12 text-lg font-semibold bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600"
              onClick={handlePurchase}
              disabled={purchasing}
            >
              {purchasing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Traitement...
                </>
              ) : (
                <>
                  <Crown className="w-5 h-5 mr-2" />
                  S'abonner maintenant
                </>
              )}
            </Button>
            
            {!billingAvailable && (
              <p className="text-xs text-center text-muted-foreground mt-3">
                💡 L'achat in-app sera disponible via Google Play Store
              </p>
            )}
          </CardContent>
        </Card>

        {/* Features List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              Tout ce qui est inclus
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {premiumFeatures.map((feature) => (
              <div key={feature.id} className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-500/20 to-orange-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">{feature.icon}</span>
                </div>
                <div>
                  <h4 className="font-medium">{feature.title}</h4>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Guarantees */}
        <div className="grid grid-cols-2 gap-3">
          <Card className="p-4 text-center">
            <Shield className="w-8 h-8 mx-auto mb-2 text-green-500" />
            <p className="text-sm font-medium">Paiement Sécurisé</p>
            <p className="text-xs text-muted-foreground">via Google Play</p>
          </Card>
          <Card className="p-4 text-center">
            <Zap className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
            <p className="text-sm font-medium">Annulation Facile</p>
            <p className="text-xs text-muted-foreground">à tout moment</p>
          </Card>
        </div>

        {/* FAQ */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Questions fréquentes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <h4 className="font-medium">Comment annuler mon abonnement ?</h4>
              <p className="text-muted-foreground">
                Vous pouvez annuler à tout moment depuis Google Play Store. 
                Votre accès Premium restera actif jusqu'à la fin de la période payée.
              </p>
            </div>
            <div>
              <h4 className="font-medium">Le paiement est-il sécurisé ?</h4>
              <p className="text-muted-foreground">
                Oui, tous les paiements sont traités de manière sécurisée par Google Play Billing.
              </p>
            </div>
            <div>
              <h4 className="font-medium">Puis-je essayer avant de m'abonner ?</h4>
              <p className="text-muted-foreground">
                La version gratuite inclut déjà de nombreuses fonctionnalités. 
                Testez l'app et passez Premium quand vous êtes prêt !
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
