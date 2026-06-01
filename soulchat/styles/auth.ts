import { StyleSheet } from "react-native";
import { Colors } from "@/constants/colors";

export const authStyles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 24,
        justifyContent: "center",
        backgroundColor: Colors.background,
    },

    title: {
        fontSize: 36,
        fontWeight: "700",
        color: Colors.text,
        textAlign: "center",
        marginBottom: 8,
    },

    subtitle: {
        fontSize: 16,
        color: Colors.textSecondary,
        textAlign: "center",
        marginBottom: 32,
    },

    input: {
        backgroundColor: Colors.surface,
        color: Colors.text,
        padding: 14,
        borderRadius: 12,
        marginBottom: 14,
        fontSize: 16,
        borderWidth: 1,
        borderColor: Colors.border,
    },

    button: {
        backgroundColor: Colors.primary,
        padding: 16,
        borderRadius: 14,
        alignItems: "center",
        marginTop: 8,
    },

    buttonText: {
        color: Colors.text,
        fontWeight: "700",
        fontSize: 16,
    },

    link: {
        color: Colors.primaryLight,
        textAlign: "center",
        marginTop: 20,
        fontSize: 15,
    },

});