import {View, Text, Pressable, StyleSheet} from 'react-native';
import { router } from 'expo-router';

import { useAuth } from '@/context/AuthContext';
import {tabsStyles} from '@/styles/tabs';

export default function HomeScreen() {
    const { user, logout } = useAuth();

    async function handleLogout() {
       await logout();
        router.replace("/login");
    }

    return (
        <View style={tabsStyles.container}>
            <Text style={tabsStyles.title}>欢迎来到 SoulChat, {user?.username}!</Text>
            <Text style={tabsStyles.subtitle}>这是你的聊天主页。</Text>
            <Text style={tabsStyles.description}>
                在这里，你可以查看你的聊天列表，加入新的聊天，或者管理你的账户设置。
            </Text>
            <Pressable style={tabsStyles.logoutButton} onPress={handleLogout}>
                <Text style={tabsStyles.logoutText}>退出登录</Text>
            </Pressable>
        </View>
    );
}
