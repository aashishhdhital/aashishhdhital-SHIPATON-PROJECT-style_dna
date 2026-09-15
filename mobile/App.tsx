import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { Pressable, StyleSheet, Text } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import InspirationScreen from './src/screens/InspirationScreen';
import StyleDnaScreen from './src/screens/StyleDnaScreen';
import GenerateScreen from './src/screens/GenerateScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import type { RootTabParamList } from './src/navigation';

const Tab = createBottomTabNavigator<RootTabParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ navigation }) => ({
            headerTitle: 'Fashion.DNA',
            headerTitleAlign: 'left',
            headerTitleStyle: {
              fontSize: 18,
              fontWeight: '700',
              color: '#2E2925',
            },
            headerRight: () => (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Open settings"
                hitSlop={8}
                onPress={() => navigation.navigate('Profile')}
                style={({ pressed }) => [styles.settingsButton, pressed && styles.settingsPressed]}
              >
                <Text style={styles.settingsIcon}>⚙</Text>
              </Pressable>
            ),
          })}
        >
          <Tab.Screen name="Inspiration" component={InspirationScreen} />
          <Tab.Screen name="Style DNA" component={StyleDnaScreen} />
          <Tab.Screen name="Generate" component={GenerateScreen} />
          <Tab.Screen name="Profile" component={ProfileScreen} />
        </Tab.Navigator>
      </NavigationContainer>
      <StatusBar style="auto" />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  settingsButton: {
    width: 36,
    height: 36,
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    borderRadius: 18,
    backgroundColor: '#F0EBE6',
  },
  settingsIcon: {
    fontSize: 18,
    lineHeight: 22,
    color: '#2E2925',
  },
  settingsPressed: {
    opacity: 0.7,
  },
});
