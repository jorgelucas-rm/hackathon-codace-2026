import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { MeUserRead, clearToken, getMe, getToken } from "../services/auth.service";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
    status: AuthStatus;
    me: MeUserRead | undefined;
    // Chamado após login/signup para o contexto reavaliar o token recém-salvo
    // (o token é gravado direto no localStorage, sem passar por estado do React).
    refresh: () => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [hasToken, setHasToken] = useState(() => !!getToken());
    const queryClient = useQueryClient();

    const { data, isLoading, isError, isSuccess } = useQuery<MeUserRead>({
        queryKey: ["me"],
        queryFn: getMe,
        enabled: hasToken,
        staleTime: 5 * 60 * 1000,
        retry: false,
    });

    // Token expirado/inválido: o backend rejeita `/api/auth/me` -> desloga.
    useEffect(() => {
        if (hasToken && isError) {
            clearToken();
            setHasToken(false);
        }
    }, [hasToken, isError]);

    const refresh = () => setHasToken(!!getToken());

    const logout = () => {
        clearToken();
        queryClient.removeQueries({ queryKey: ["me"] });
        setHasToken(false);
    };

    const status: AuthStatus = !hasToken
        ? "unauthenticated"
        : isLoading
            ? "loading"
            : isSuccess
                ? "authenticated"
                : "unauthenticated";

    return (
        <AuthContext.Provider value={{ status, me: data, refresh, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth precisa ser usado dentro de <AuthProvider>");
    return ctx;
}
