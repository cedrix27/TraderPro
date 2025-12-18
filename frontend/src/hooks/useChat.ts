"use client";

import { useState, useCallback } from "react";
import { chatApi, ChatResponse, ApiError } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  analysis?: any;
  signal?: any;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
}

const INITIAL_MESSAGE: ChatMessage = {
  id: "initial",
  role: "assistant",
  content: `Bonjour ! Je suis votre assistant de trading IA spécialisé sur le Bitcoin. Je peux vous aider à :

• Analyser les tendances actuelles du marché
• Identifier les zones de support et résistance
• Proposer des plans de trading adaptés à votre profil
• Expliquer les indicateurs techniques

Comment puis-je vous aider aujourd'hui ?`,
  timestamp: new Date(),
};

/**
 * Hook pour gérer le chat avec l'assistant IA
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Ajouter le message de l'utilisateur
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: message.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.sendMessage(message);

      // Ajouter la réponse de l'assistant
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message,
        timestamp: new Date(),
        analysis: response.analysis,
        signal: response.signal,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      let errorMessage = "Erreur lors de l'envoi du message";

      if (err instanceof ApiError) {
        errorMessage = err.message;
      }

      // Ajouter un message d'erreur
      const errorAssistantMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Désolé, une erreur s'est produite : ${errorMessage}. Veuillez réessayer.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorAssistantMessage]);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([INITIAL_MESSAGE]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearMessages };
}
