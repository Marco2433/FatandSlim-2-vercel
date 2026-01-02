import { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext();

// Translations
const translations = {
  fr: {
    // Navigation
    dashboard: 'Tableau de bord',
    nutrition: 'Nutrition',
    workouts: 'Entraînements',
    scanner: 'Scanner',
    community: 'Communauté',
    profile: 'Profil',
    bariatric: 'By-pass/Sleeve',
    
    // Common
    loading: 'Chargement...',
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    share: 'Partager',
    close: 'Fermer',
    back: 'Retour',
    next: 'Suivant',
    finish: 'Terminer',
    search: 'Rechercher',
    filter: 'Filtrer',
    
    // Dashboard
    welcome: 'Bienvenue',
    dailyChallenges: 'Défis du jour',
    appointments: 'Rendez-vous',
    todayRecipes: 'Recettes du jour',
    caloriesConsumed: 'Calories consommées',
    caloriesBurned: 'Calories brûlées',
    
    // Workouts
    allCategories: 'Toutes',
    favorites: 'Favoris',
    addToFavorites: 'Ajouter aux favoris',
    removeFromFavorites: 'Retirer des favoris',
    addToAgenda: 'Ajouter à l\'agenda',
    shareWorkout: 'Partager',
    completed: 'Terminé !',
    
    // Profile
    settings: 'Paramètres',
    language: 'Langue',
    logout: 'Déconnexion',
    deleteAccount: 'Supprimer le compte',
    
    // Messages
    success: 'Succès',
    error: 'Erreur',
    saved: 'Enregistré',
    shared: 'Partagé',
  },
  en: {
    // Navigation
    dashboard: 'Dashboard',
    nutrition: 'Nutrition',
    workouts: 'Workouts',
    scanner: 'Scanner',
    community: 'Community',
    profile: 'Profile',
    bariatric: 'Bypass/Sleeve',
    
    // Common
    loading: 'Loading...',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    share: 'Share',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    finish: 'Finish',
    search: 'Search',
    filter: 'Filter',
    
    // Dashboard
    welcome: 'Welcome',
    dailyChallenges: 'Daily Challenges',
    appointments: 'Appointments',
    todayRecipes: 'Today\'s Recipes',
    caloriesConsumed: 'Calories Consumed',
    caloriesBurned: 'Calories Burned',
    
    // Workouts
    allCategories: 'All',
    favorites: 'Favorites',
    addToFavorites: 'Add to favorites',
    removeFromFavorites: 'Remove from favorites',
    addToAgenda: 'Add to agenda',
    shareWorkout: 'Share',
    completed: 'Completed!',
    
    // Profile
    settings: 'Settings',
    language: 'Language',
    logout: 'Logout',
    deleteAccount: 'Delete Account',
    
    // Messages
    success: 'Success',
    error: 'Error',
    saved: 'Saved',
    shared: 'Shared',
  }
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('language') || 'fr';
  });

  useEffect(() => {
    localStorage.setItem('language', language);
    document.documentElement.lang = language;
  }, [language]);

  const t = (key) => {
    return translations[language]?.[key] || translations.fr[key] || key;
  };

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'fr' ? 'en' : 'fr');
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};

export default LanguageContext;
