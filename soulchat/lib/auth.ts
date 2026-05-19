import AsyncStorage from "@react-native-async-storage/async-storage";

const TOKEN_KEY = "soulchat_access_token";
const USER_KEY = "soulchat_user";

export type StoredUser = {
    user_id: string;
    username: string;
    email: string;
};

// Save login info after login/register
export async function saveAuth(
    token: string,
    user: StoredUser
) {
    await AsyncStorage.setItem(TOKEN_KEY, token);
    await AsyncStorage.setItem(
        USER_KEY, 
        JSON.stringify(user)
    );
}

// Get JWT token
export async function getToken() {
    return AsyncStorage.getItem(TOKEN_KEY);
}

// Get locally saved user info
export async function getStoredUser(): Promise<StoredUser | null> {
    const raw = await AsyncStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        console.error("Failed to parse stored user", e);
        return null;
    }
}

// Logout
export async function clearAuth() {
    await AsyncStorage.removeItem(TOKEN_KEY);
    await AsyncStorage.removeItem(USER_KEY);
}

// check if user is logged in 
export async function isLoggedIn() {
    const token = await getToken();
    return !!token;
}