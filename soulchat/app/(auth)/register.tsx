import { useState } from "react";
import {
    View,
    Text,
    TextInput,
    Pressable,
    Alert,
} from "react-native";

import { router } from "expo-router";
import { authStyles } from "@/styles/auth";
import { register } from "@/lib/api";

export default function RegisterScreen() {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    async function handleRegister() {
        try {
            await register(username, email, password);

            Alert.alert("Success", "Registration successful! Please log in.");
            router.replace("/login");
        } catch (error: any){
            Alert.alert(
                "Registration Failed",
                error.message || "Please try again"
            );
        }
    }

    return (
        <View style={authStyles.container}>
            <Text style={authStyles.title}>创建账户</Text>
            <Text style={authStyles.subtitle}>
                加入 SoulChat，创造你的专属聊天体验！
            </Text>
            <TextInput
                style={authStyles.input}
                placeholder="用户名"
                placeholderTextColor="#777"
                value={username}
                onChangeText={setUsername}
                autoCapitalize="none"
            />
            <TextInput
                style={authStyles.input}
                placeholder="邮箱"
                placeholderTextColor="#777"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
            />
            <TextInput
                style={authStyles.input}
                placeholder="密码"
                placeholderTextColor="#777"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            <Pressable style={authStyles.button} onPress={handleRegister}>
                <Text style={authStyles.buttonText}>注册</Text>
            </Pressable>

            <Pressable onPress={() => router.replace("/login")}>
                <Text style={authStyles.link}>已有账户？立即登录</Text>
            </Pressable>
        </View>
    )
}
