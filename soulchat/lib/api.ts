const API_BASE_URL = "http://localhost:8000";

async function request<T>(
    path: string,
    options: RequestInit = {}, // include method, body, headers, etc.
    token?: string | null // Optional JWT token
): Promise<T> {
    // Creates request headers
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string> || {}),
    };

    // Backend knows who the user is
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    // Makes the API request
    const res = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers,
    });

    const data = await res.json().catch(() => null);
    
    if (!res.ok) {
        throw new Error(data?.detail || "An error occurred");
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

export async function updateMe(
    payload: any,
    token: string
){
    return request<any>(
        "/me", 
        {
            method: "PUT",
            body: JSON.stringify(payload),
        }, 
        token
    );
}

export async function getCharacters(token: string){
    return request<any[]>("/characters", {}, token);
}

export async function getCharacter( 
    characterId: string,
    token: string
){
    return request<any>(
        `/characters/${characterId}`, 
        {}, 
        token
    );
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

export async function getMessages(
    conversationId: string,
    token: string
){
    return request<any[]>(
        `/conversations/${conversationId}/messages`, 
        {}, 
        token
    );
}

export async function deleteMessagesAfter(
    conversationId: string,
    messageId: string,
    token: string
){
    return request<any>(
        `/conversations/${conversationId}/messages/after/${messageId}`,
        {
            method: "DELETE",
        },
        token
    );
}

export async function regenerateMessage(
    conversationId: string,
    messageId: string,
    newMessage: string,
    token: string
){
    return request<any>(
        `/conversations/${conversationId}/messages/${messageId}/regenerate`,
        {
            method: "POST",
            body: JSON.stringify({ 
                new_message: newMessage 
            }),
        },
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
        `/conversations/${conversationId}/suggested_replies`, 
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

export async function updateCharacter(
    characterId: string,
    payload: any,
    token: string
){
    return request<any>(
        `/characters/${characterId}`, 
        {
            method: "PUT",
            body: JSON.stringify(payload),
        }, 
        token
    );
}

export async function deleteCharacter(
    characterId: string,
    token: string
){
    return request<any>(
        `/characters/${characterId}`, 
        {
            method: "DELETE",
        }, 
        token
    );
}

export async function uploadImage(
    file: {
        uri: string;
        type: string;
        name: string;
    },
    token: string
){
    const formData = new FormData();

    formData.append("file", {
        uri: file.uri,
        name: file.name,
        type: file.type,
    } as any);

    const res = await fetch(
        `${API_BASE_URL}/upload/images/upload`,{
            method: "POST",
            body: formData,
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

    const data = await res.json().catch(() => null);

    if (!res.ok) {
        throw new Error(data?.detail || "An error occurred");
    }

    return data;
}

export async function getImages(token: string){
    return request<any[]>(
        "/images", 
        {}, 
        token
    );
}

export async function getImage(
    imageId: string,
    token: string

){
    return request<any>(
        `/images/${imageId}`, 
        {}, 
        token
    );
}

export async function deleteImage(
    imageId: string,
    token: string
){
    return request<any>(
        `/images/${imageId}`, 
        {
            method: "DELETE",
        }, 
        token
    );
}
