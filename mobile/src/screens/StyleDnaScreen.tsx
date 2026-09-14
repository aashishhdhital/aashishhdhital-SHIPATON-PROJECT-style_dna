import { StyleSheet, Text, View } from 'react-native';

export default function StyleDnaScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>YOUR PROFILE</Text>
      <Text style={styles.title}>Style DNA</Text>
      <Text style={styles.subtitle}>Your personal style story starts here.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#EEF2F1',
  },
  eyebrow: {
    marginBottom: 8,
    color: '#3F716A',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  title: {
    color: '#253331',
    fontSize: 36,
    fontWeight: '700',
  },
  subtitle: {
    marginTop: 12,
    color: '#5F706D',
    fontSize: 17,
  },
});
