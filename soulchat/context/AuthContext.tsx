import React, {
    createContext,
    useContext,
    useEffect,
    useState,
    ReactNode,
} from 'react';

import {login as loginApi} from "@/lib/api";
import {
    saveAuth,
    getToken,
    getStoredUser,
    clearAuth,
    StoredUser,
} from "@/lib/auth";

type AuthContextType = {
    token: string | null;
    user: StoredUser | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthProviderProps = {
    children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
    const [token, setToken] = useState<string | null>(null);
    const [user, setUser] = useState<StoredUser | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAuth();
    }, []);

    async function loadAuth() {
        try {
            const savedToken = await getToken();
            const savedUser = await getStoredUser();
            if (savedToken && savedUser) {
                setToken(savedToken);
                setUser(savedUser);
            }
        } finally {
            setLoading(false);
        }
    }

    async function login(email: string, password: string) {
        const data = await loginApi(email, password);

        const storedUser: StoredUser = {
            user_id: data.user_id,
            username: data.username,
            email: data.email,
        };

        await saveAuth(data.access_token, storedUser);

        setToken(data.access_token);
        setUser(storedUser);
    }

    async function logout() {
        await clearAuth();
        setToken(null);
        setUser(null);
    }

    return (
        <AuthContext.Provider
            value={{
                token,
                user,
                loading,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}