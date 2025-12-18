"use client";

import { useState, useEffect, useCallback } from "react";
import { healthApi, ApiError } from "@/lib/api";

interface UseApiHealthReturn {
  isConnected: boolean;
  isChecking: boolean;
  error: string | null;
  checkConnection: () => Promise<void>;
}

/**
 * Hook pour vérifier si le backend est en ligne
 */
export function useApiHealth(): UseApiHealthReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkConnection = useCallback(async () => {
    try {
      setIsChecking(true);
      setError(null);
      await healthApi.check();
      setIsConnected(true);
    } catch (err) {
      setIsConnected(false);
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Impossible de se connecter au serveur");
      }
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();

    // Vérifier la connexion toutes les 30 secondes
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  return { isConnected, isChecking, error, checkConnection };
}
