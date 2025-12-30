import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft } from 'lucide-react';

export default function PrivacyPolicyPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background pb-safe">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-4 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="font-heading text-xl font-bold">Politique de confidentialité</h1>
        </div>
      </header>

      <main className="p-4 max-w-2xl mx-auto">
        <Card>
          <CardContent className="p-6 prose prose-sm dark:prose-invert max-w-none">
            <p className="text-muted-foreground text-sm mb-6">
              Dernière mise à jour : 30 décembre 2024
            </p>

            <h2 className="text-lg font-semibold mt-6 mb-3">1. Introduction</h2>
            <p>
              Bienvenue sur <strong>Fat & Slim</strong>. Nous accordons une grande importance à la protection 
              de vos données personnelles. Cette politique de confidentialité explique comment nous collectons, 
              utilisons, stockons et protégeons vos informations lorsque vous utilisez notre application.
            </p>

            <h2 className="text-lg font-semibold mt-6 mb-3">2. Données collectées</h2>
            <p>Nous collectons les types de données suivants :</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Informations de compte</strong> : nom, adresse e-mail, mot de passe (crypté)</li>
              <li><strong>Données de profil</strong> : âge, sexe, taille, poids, objectifs de santé</li>
              <li><strong>Données nutritionnelles</strong> : aliments consommés, calories, macronutriments</li>
              <li><strong>Données d'activité</strong> : nombre de pas, exercices, calories brûlées</li>
              <li><strong>Données de progression</strong> : historique de poids, IMC</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">3. Utilisation des données</h2>
            <p>Vos données sont utilisées pour :</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Personnaliser votre expérience et vos recommandations nutritionnelles</li>
              <li>Calculer vos besoins caloriques et objectifs personnalisés</li>
              <li>Suivre votre progression vers vos objectifs de santé</li>
              <li>Générer des rapports de progression</li>
              <li>Améliorer nos services et fonctionnalités</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">4. Stockage et sécurité</h2>
            <p>
              Vos données sont stockées de manière sécurisée sur des serveurs protégés. Nous utilisons :
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Chiffrement SSL/TLS pour toutes les communications</li>
              <li>Mots de passe hashés avec des algorithmes sécurisés (bcrypt)</li>
              <li>Authentification par tokens JWT</li>
              <li>Accès restreint aux bases de données</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">5. Partage des données</h2>
            <p>
              <strong>Nous ne vendons jamais vos données personnelles.</strong> Vos informations ne sont 
              partagées qu'avec :
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Nos prestataires techniques nécessaires au fonctionnement de l'application</li>
              <li>Les autorités légales si requis par la loi</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">6. Vos droits</h2>
            <p>Conformément au RGPD, vous disposez des droits suivants :</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Droit d'accès</strong> : consulter vos données personnelles</li>
              <li><strong>Droit de rectification</strong> : modifier vos informations</li>
              <li><strong>Droit à l'effacement</strong> : supprimer votre compte et vos données</li>
              <li><strong>Droit à la portabilité</strong> : exporter vos données (PDF)</li>
              <li><strong>Droit d'opposition</strong> : vous opposer au traitement de vos données</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">7. Cookies et stockage local</h2>
            <p>
              L'application utilise le stockage local de votre appareil pour :
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Maintenir votre session de connexion</li>
              <li>Sauvegarder vos préférences d'affichage</li>
              <li>Améliorer les performances de l'application</li>
            </ul>

            <h2 className="text-lg font-semibold mt-6 mb-3">8. Conservation des données</h2>
            <p>
              Vos données sont conservées tant que votre compte est actif. En cas de suppression de compte, 
              vos données personnelles seront effacées dans un délai de 30 jours, à l'exception des données 
              nécessaires pour des obligations légales.
            </p>

            <h2 className="text-lg font-semibold mt-6 mb-3">9. Modifications</h2>
            <p>
              Cette politique de confidentialité peut être mise à jour occasionnellement. Nous vous 
              informerons de tout changement significatif par notification dans l'application.
            </p>

            <h2 className="text-lg font-semibold mt-6 mb-3">10. Contact</h2>
            <p>
              Pour toute question concernant cette politique de confidentialité ou vos données personnelles, 
              vous pouvez nous contacter à :
            </p>
            <p className="mt-2">
              <strong>Email</strong> : contact@fatandslim.app<br />
              <strong>Application</strong> : Fat & Slim
            </p>

            <div className="mt-8 p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                En utilisant Fat & Slim, vous acceptez cette politique de confidentialité. 
                Si vous n'acceptez pas ces termes, veuillez ne pas utiliser l'application.
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
