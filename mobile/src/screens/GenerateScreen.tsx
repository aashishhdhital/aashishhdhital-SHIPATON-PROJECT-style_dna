import { StyleSheet, Text, View } from 'react-native';

export default function GenerateScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>CREATE</Text>
      <Text style={styles.title}>Generate</Text>
      <Text style={styles.subtitle}>Turn your style into something new.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F2F0F5',
  },
  eyebrow: {
    marginBottom: 8,
    color: '#6D5680',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#312B37',
    fontSize: 36,
    fontWeight: '700',
  },
  subtitle: {
    marginTop: 12,
    color: '#6E6574',
    fontSize: 17,
  },
});
