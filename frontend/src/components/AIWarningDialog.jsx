import { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Sparkles, AlertTriangle, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AIWarningDialog({ 
  open, 
  onOpenChange, 
  onConfirm, 
  title = "Utilisation de l'IA",
  description = "Cette action utilise un crédit IA."
}) {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open) {
      fetchUsage();
    }
  }, [open]);

  const fetchUsage = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/ai/usage`, { withCredentials: true });
      setUsage(response.data);
    } catch (error) {
      console.error('Error fetching AI usage:', error);
    } finally {
      setLoading(false);
    }
  };

  const isLimitReached = usage?.remaining === 0;

  const handleConfirm = () => {
    onOpenChange(false);
    if (onConfirm) {
      onConfirm();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isLimitReached ? (
              <AlertTriangle className="w-5 h-5 text-destructive" />
            ) : (
              <Sparkles className="w-5 h-5 text-primary" />
            )}
            {title}
          </DialogTitle>
          <DialogDescription>
            {description}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : isLimitReached ? (
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
              <p className="text-sm font-medium text-destructive">
                ⚠️ Limite quotidienne atteinte !
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Vous avez utilisé vos {usage?.limit} appels IA gratuits aujourd'hui. 
                Revenez demain pour de nouveaux crédits !
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="p-4 bg-primary/10 border border-primary/30 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Crédits IA disponibles</span>
                  <span className="text-lg font-bold text-primary">
                    {usage?.remaining}/{usage?.limit}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${((usage?.limit - usage?.used) / usage?.limit) * 100}%` }}
                  />
                </div>
              </div>
              
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <p className="text-sm text-amber-700 dark:text-amber-400">
                  💡 <strong>Rappel :</strong> L'utilisation de l'IA est limitée à {usage?.limit} appels gratuits par jour.
                  Utilisez-les judicieusement !
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          {!isLimitReached && (
            <Button onClick={handleConfirm}>
              <Sparkles className="w-4 h-4 mr-2" />
              Utiliser 1 crédit IA
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
