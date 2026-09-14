import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import InspirationScreen from './src/screens/InspirationScreen';
import StyleDnaScreen from './src/screens/StyleDnaScreen';
import GenerateScreen from './src/screens/GenerateScreen';
import ProfileScreen from './src/screens/ProfileScreen';

export type RootTabParamList = {
  Inspiration: undefined;
  'Style DNA': undefined;
  Generate: undefined;
  Profile: undefined;
};

const Tab = createBottomTabNavigator<RootTabParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Tab.Navigator>
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
