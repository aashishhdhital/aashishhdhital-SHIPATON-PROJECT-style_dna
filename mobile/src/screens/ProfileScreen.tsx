import { StyleSheet, Text, View } from 'react-native';

export default function ProfileScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>ACCOUNT</Text>
      <Text style={styles.title}>Profile</Text>
      <Text style={styles.subtitle}>Manage your preferences and wardrobe.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F5F1EA',
  },
  eyebrow: {
    marginBottom: 8,
    color: '#8A6B3F',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#332D27',
    fontSize: 36,
    fontWeight: '700',
  },
  subtitle: {
    marginTop: 12,
    color: '#75695D',
    fontSize: 17,
  },
});
