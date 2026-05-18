const API_BASE_URL = "http://localhost:8000";

async function request<T>(
    path: string,
    options: RequestInit = {},
    token?: string | null
): Promise<T> {
    const headers: HeadersInit = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });

    const data = await res.json().catch(() => null);
    
    if (!res.ok) {
        throw new Error(data?.message || "An error occurred");
    }

    return data as T;
}

export async function login(email: string, password: string) {
    return request<{
        access_token: string;
        token_type: string;
        user_id: string;
        username: string;
        email: string;
    }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
}

export async function register(username: string, email: string, password: string) {
    return request<{
        user_id: string;
        username: string;
        email: string;
    }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, email, password }),
    });
}

export async function getMe(token: string) {
    return request<{
        user_id: string;
        username: string;
        email: string;
        role: string;
        persona_preference?: string | null;
    }>("/me", {}, token);
}

export async function getCharacters(token: string){
    return request<any[]>("/characters", {}, token);
}

export async function getCharacter(token: string, characterId: string){
    return request<any>(`/characters/${characterId}`, {}, token);
}

export async function createCharacter(
    payload: any,
    token: string
){
    return request<any>("/characters", {
        method: "POST",
        body: JSON.stringify(payload),
    }, token);
}

export async function getConversations(token: string){
    return request<any[]>("/conversations", {}, token);
}

export async function getMessages(token: string, conversationId: string){
    return request<any[]>(
        `/conversations/${conversationId}/messages`, 
        {}, 
        token
    );
}

export async function sendChat(
    payload: {
        character_id: string;
        message: string;
        conversation_id?: string | null;
    },
    token: string
) {
    return request<{
        reply: string;
        conversation_id: string;
    }>("/chat", {
        method: "POST",
        body: JSON.stringify(payload),
    }, token);
}

export async function suggestReplies(
    conversationId: string,
    token: string
){
    return request<{ suggestions: string[] }>(
        `/conversations/${conversationId}/suggest_replies`, 
        {
            method: "POST",
        }, 
        token
    );
}

export async function continueCharacter(
    conversationId: string,
    token: string
){
    return request<{
        reply: string;
        conversation_id: string;
        assistant_message_id: string;
    }>(
        `/conversations/${conversationId}/continue`, 
        {
            method: "POST",
        }, 
        token
    );
}