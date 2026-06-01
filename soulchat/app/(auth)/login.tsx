import { useState } from "react";
import {
    View,
    Text,
    TextInput,
    Pressable,
    Alert,
} from "react-native";

import { router } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { authStyles } from "@/styles/auth";

export default function LoginScreen() {
    const { login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    async function handleLogin() {
        try {
            await login(email, password);

            router.replace("/(tabs)");
        } catch (error: any){
            Alert.alert(
                "Login Failed",
                error.message || "Please try again"
            );
        }
    }

    return (
        <View style={authStyles.container}>
            <Text style={authStyles.title}>
                SoulChat
            </Text>

            <Text style={authStyles.subtitle}>
                开始你的聊天之旅吧！
            </Text>

            <TextInput
                style={authStyles.input}
                placeholder="Email"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                />

            <TextInput
                style={authStyles.input}
                placeholder="Password"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />

            <Pressable 
                onPress={handleLogin} 
                style={authStyles.button}
            >

                <Text style={authStyles.buttonText}>登录</Text>

            </Pressable>

            <Pressable
                onPress={() => router.push("/register")}>

                <Text style={authStyles.link}>
                    没有账号？注册一个
                </Text>

            </Pressable>

        </View>
    );
}