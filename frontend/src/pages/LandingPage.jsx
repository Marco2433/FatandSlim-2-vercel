import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  Camera, 
  Utensils, 
  Dumbbell, 
  TrendingUp, 
  Sparkles, 
  ChevronRight,
  Star,
  Zap
} from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Camera,
      title: 'Scan IA',
      description: 'Photographiez vos repas pour une analyse nutritionnelle instantanée',
      color: 'bg-secondary text-secondary-foreground'
    },
    {
      icon: Utensils,
      title: 'Menus personnalisés',
      description: 'Plans alimentaires adaptés à vos objectifs et préférences',
      color: 'bg-accent text-accent-foreground'
    },
    {
      icon: Dumbbell,
      title: 'Coaching sportif',
      description: 'Programmes d\'entraînement sur mesure pour tous niveaux',
      color: 'bg-primary text-primary-foreground'
    },
    {
      icon: TrendingUp,
      title: 'Suivi intelligent',
      description: 'Visualisez votre progression avec des statistiques détaillées',
      color: 'bg-chart-4 text-white'
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: 'url(https://images.unsplash.com/photo-1760879946075-ddb8432a322d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwzfHxwZXJzb24lMjBydW5uaW5nJTIwb3V0ZG9vciUyMG1vcm5pbmd8ZW58MHx8fHwxNzY3MDExNTQ3fDA&ixlib=rb-4.1.0&q=85)'
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-b from-background/80 via-background/60 to-background" />
        </div>

        <div className="relative px-4 pt-8 pb-16 md:pt-16 md:pb-24">
          {/* Logo */}
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-2">
              <img 
                src="https://customer-assets.emergentagent.com/job_c618c56f-e2f2-438f-a5f9-200244f81f08/artifacts/8fl7ig96_11053968.png" 
                alt="Fat & Slim Logo" 
                className="w-10 h-10 rounded-xl object-contain"
              />
              <span className="font-heading font-bold text-xl">Fat & Slim</span>
            </div>
            <Button 
              variant="ghost" 
              onClick={() => navigate('/login')}
              data-testid="login-btn-header"
            >
              Connexion
            </Button>
          </div>

          {/* Hero Content */}
          <div className="max-w-2xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">Coaching IA personnalisé</span>
            </div>
            
            <h1 className="font-heading text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Transformez votre corps avec{' '}
              <span className="text-gradient">l'intelligence artificielle</span>
            </h1>
            
            <p className="text-lg text-muted-foreground mb-8 max-w-xl mx-auto">
              Fat & Slim analyse votre profil, vos habitudes et vos objectifs pour créer 
              un programme nutrition et sport 100% personnalisé.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="rounded-full shadow-glow px-8"
                onClick={() => navigate('/register')}
                data-testid="get-started-btn"
              >
                Commencer gratuitement
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="rounded-full"
                onClick={() => navigate('/login')}
                data-testid="login-btn"
              >
                J'ai déjà un compte
              </Button>
            </div>

            {/* Social Proof */}
            <div className="flex items-center justify-center gap-4 mt-8">
              <div className="flex -space-x-2">
                {[
                  "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face",
                  "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
                  "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
                  "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face"
                ].map((img, i) => (
                  <img 
                    key={i}
                    src={img}
                    alt={`User ${i+1}`}
                    className="w-8 h-8 rounded-full border-2 border-background object-cover"
                  />
                ))}
              </div>
              <div className="text-sm text-muted-foreground">
                <span className="text-foreground font-semibold">+10 000</span> utilisateurs actifs
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 py-16 md:py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
              Tout ce dont vous avez besoin
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Une application complète pour atteindre vos objectifs de forme et de santé
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="group p-6 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300 hover:-translate-y-1"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="font-heading font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Food Section */}
      <section className="px-4 py-16 bg-muted/50">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
                Scannez, analysez, améliorez
              </h2>
              <p className="text-muted-foreground mb-6">
                Notre IA reconnaît instantanément vos aliments et calcule les valeurs 
                nutritionnelles. Obtenez un score Nutri-Score et des recommandations 
                personnalisées pour chaque repas.
              </p>
              <ul className="space-y-3">
                {[
                  'Reconnaissance photo des aliments',
                  'Calcul calories, protéines, glucides, lipides',
                  'Score nutritionnel de A à E',
                  'Suggestions d\'alternatives plus saines'
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                      <Star className="w-3 h-3 text-primary-foreground" />
                    </div>
                    <span className="text-sm">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1761315600943-d8a5bb0c499f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxoZWFsdGh5JTIwZm9vZCUyMGJvd2wlMjBmcmVzaCUyMGluZ3JlZGllbnRzJTIwb3ZlcmhlYWR8ZW58MHx8fHwxNzY3MDExNTMzfDA&ixlib=rb-4.1.0&q=85"
                alt="Healthy food"
                className="rounded-2xl shadow-glass"
              />
              <div className="absolute -bottom-4 -left-4 bg-card rounded-xl p-4 shadow-lg border border-border">
                <div className="flex items-center gap-3">
                  <div className="nutri-badge nutri-a">A</div>
                  <div>
                    <p className="font-semibold text-sm">Salade Quinoa</p>
                    <p className="text-xs text-muted-foreground">320 kcal</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-16 md:py-24">
        <div className="max-w-3xl mx-auto text-center">
          <div className="p-8 md:p-12 rounded-3xl gradient-primary">
            <h2 className="font-heading text-3xl md:text-4xl font-bold text-primary-foreground mb-4">
              Prêt à transformer votre vie ?
            </h2>
            <p className="text-primary-foreground/80 mb-8 max-w-lg mx-auto">
              Rejoignez des milliers d'utilisateurs qui ont déjà atteint leurs objectifs 
              grâce à Fat & Slim
            </p>
            <Button 
              size="lg" 
              variant="secondary"
              className="rounded-full px-8 shadow-glow-purple"
              onClick={() => navigate('/register')}
              data-testid="cta-btn"
            >
              Commencer maintenant
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-4 py-8 border-t border-border">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_c618c56f-e2f2-438f-a5f9-200244f81f08/artifacts/8fl7ig96_11053968.png" 
              alt="Fat & Slim Logo" 
              className="w-8 h-8 rounded-lg object-contain"
            />
            <span className="font-heading font-bold">Fat & Slim</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2024 Fat & Slim. Tous droits réservés.
          </p>
        </div>
      </footer>
    </div>
  );
}
