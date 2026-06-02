import {StyleSheet} from 'react-native';
import {Colors} from "@/constants/colors";

export const tabsStyles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: Colors.background,
        justifyContent: "center",
        alignItems: "center",
        padding: 24,
    },
    title: {
        fontSize: 36,
        fontWeight: "700",
        color: Colors.text,
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 18,
        color: Colors.textSecondary,
        marginBottom: 24,
    },
    description: {
        color: Colors.textMuted,
        textAlign: "center",
        marginBottom: 32,
    },
    logoutButton: {
        backgroundColor: Colors.primary,
        paddingVertical: 14,
        paddingHorizontal: 32,
        borderRadius: 14,
    },
    logoutText: {
        color: Colors.text,
        fontWeight: "700",
        fontSize: 16,
    },
});