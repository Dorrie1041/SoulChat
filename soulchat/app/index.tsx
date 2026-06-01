import { useEffect } from "react";
import { View, ActivityIndicator } from "react-native";
import { router } from "expo-router";

import { useAuth } from "@/context/AuthContext";
import { Colors } from "@/constants/colors";

export default function IndexScreen() {
    const { token, loading } = useAuth();

    useEffect(() => {
        if (loading) return;

        if (token) {
            router.replace("/(tabs)");
        } else {
            router.replace("/(auth)/login");
        }
    }, [token, loading]);

    return (
        <View style={{ 
            flex: 1, 
            justifyContent: "center", 
            alignItems: "center", 
            backgroundColor: Colors.background }}>
            <ActivityIndicator color={Colors.primary} />
        </View>
    );
}