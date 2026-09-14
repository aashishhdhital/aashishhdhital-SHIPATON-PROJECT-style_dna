import { StyleSheet, Text, View } from 'react-native';

export default function InspirationScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>DISCOVER</Text>
      <Text style={styles.title}>Inspiration</Text>
      <Text style={styles.subtitle}>Find looks that feel like you.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#F7F3EE',
  },
  eyebrow: {
    marginBottom: 8,
    color: '#A15C38',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#2E2925',
    fontSize: 36,
    fontWeight: '700',
  },
  subtitle: {
    marginTop: 12,
    color: '#6E625A',
    fontSize: 17,
  },
});
