import { useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

type PreferenceRowProps = {
  label: string;
  description: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
};

const profileSummary = [
  { label: 'Top style', value: 'Minimalist' },
  { label: 'Secondary style', value: 'Streetwear' },
  { label: 'Inspiration count', value: '5' },
  { label: 'Recommendations rated', value: '3' },
];

function PreferenceRow({ label, description, value, onValueChange }: PreferenceRowProps) {
  return (
    <View style={styles.preferenceRow}>
      <View style={styles.preferenceCopy}>
        <Text style={styles.preferenceLabel}>{label}</Text>
        <Text style={styles.preferenceDescription}>{description}</Text>
      </View>
      <Switch
        accessibilityLabel={label}
        onValueChange={onValueChange}
        trackColor={{ false: '#D8D1C8', true: '#C7D9D5' }}
        thumbColor={value ? '#3F716A' : '#F8F7F4'}
        value={value}
      />
    </View>
  );
}

export default function ProfileScreen() {
  const [useFeedback, setUseFeedback] = useState(true);
  const [showMatchPercentage, setShowMatchPercentage] = useState(true);

  const showActionConfirmation = (title: string, message: string) => {
    Alert.alert(title, message, [{ text: 'Done' }]);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>ACCOUNT</Text>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.subtitle}>Your space for preferences and style details.</Text>

        <View style={styles.userCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>AM</Text>
          </View>
          <View style={styles.userCopy}>
            <Text style={styles.userName}>Alex Morgan</Text>
            <Text style={styles.userEmail}>Guest user</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your style at a glance</Text>
          <View style={styles.summaryCard}>
            {profileSummary.map((item, index) => (
              <View
                key={item.label}
                style={[styles.summaryRow, index === profileSummary.length - 1 && styles.lastRow]}
              >
                <Text style={styles.summaryLabel}>{item.label}</Text>
                <Text style={styles.summaryValue}>{item.value}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          <View style={styles.preferenceCard}>
            <PreferenceRow
              description="Use your reactions to refine future looks"
              label="Use feedback to improve recommendations"
              onValueChange={setUseFeedback}
              value={useFeedback}
            />
            <View style={styles.rowDivider} />
            <PreferenceRow
              description="See how closely each look matches your style"
              label="Show style match percentage"
              onValueChange={setShowMatchPercentage}
              value={showMatchPercentage}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your data</Text>
          <View style={styles.actionsCard}>
            <Pressable
              accessibilityRole="button"
              onPress={() =>
                showActionConfirmation(
                  'Style DNA reset',
                  'Your local mock Style DNA can be rebuilt from new inspiration later.',
                )
              }
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.actionIconText}>↻</Text>
              </View>
              <View style={styles.actionCopy}>
                <Text style={styles.actionLabel}>Reset local Style DNA</Text>
                <Text style={styles.actionDescription}>Remove the current mock style summary</Text>
              </View>
              <Text style={styles.chevron}>›</Text>
            </Pressable>
            <View style={styles.rowDivider} />
            <Pressable
              accessibilityRole="button"
              onPress={() =>
                showActionConfirmation(
                  'Inspiration cleared',
                  'Your selected inspiration is stored locally for now and can be added again later.',
                )
              }
              style={({ pressed }) => [styles.actionRow, pressed && styles.pressed]}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.actionIconText}>×</Text>
              </View>
              <View style={styles.actionCopy}>
                <Text style={styles.actionLabel}>Clear selected inspiration</Text>
                <Text style={styles.actionDescription}>Remove local inspiration selections</Text>
              </View>
              <Text style={styles.chevron}>›</Text>
            </Pressable>
          </View>
        </View>

        <View style={styles.futureRow}>
          <View style={styles.futureIcon}>
            <Text style={styles.futureIconText}>◌</Text>
          </View>
          <View style={styles.futureCopy}>
            <Text style={styles.futureTitle}>Sign in / account sync coming later</Text>
            <Text style={styles.futureDescription}>Your preferences currently stay on this device.</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F1EA',
  },
  content: {
    padding: 24,
    paddingBottom: 32,
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
    lineHeight: 25,
  },
  userCard: {
    minHeight: 92,
    marginTop: 24,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  avatar: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#D8C5AD',
  },
  avatarText: {
    color: '#5F4932',
    fontSize: 17,
    fontWeight: '700',
  },
  userCopy: {
    marginLeft: 14,
  },
  userName: {
    color: '#332D27',
    fontSize: 18,
    fontWeight: '700',
  },
  userEmail: {
    marginTop: 5,
    color: '#8A7A6B',
    fontSize: 14,
  },
  section: {
    marginTop: 28,
  },
  sectionTitle: {
    color: '#332D27',
    fontSize: 18,
    fontWeight: '700',
  },
  summaryCard: {
    marginTop: 14,
    paddingHorizontal: 18,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  summaryRow: {
    minHeight: 51,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: 1,
    borderBottomColor: '#EEE8E0',
  },
  lastRow: {
    borderBottomWidth: 0,
  },
  summaryLabel: {
    color: '#75695D',
    fontSize: 14,
  },
  summaryValue: {
    color: '#514438',
    fontSize: 14,
    fontWeight: '700',
  },
  preferenceCard: {
    marginTop: 14,
    paddingHorizontal: 18,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  preferenceRow: {
    minHeight: 78,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  preferenceCopy: {
    flex: 1,
  },
  preferenceLabel: {
    color: '#514438',
    fontSize: 14,
    fontWeight: '700',
  },
  preferenceDescription: {
    marginTop: 4,
    color: '#8A7A6B',
    fontSize: 12,
    lineHeight: 17,
  },
  rowDivider: {
    height: 1,
    backgroundColor: '#EEE8E0',
  },
  actionsCard: {
    marginTop: 14,
    paddingHorizontal: 18,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  actionRow: {
    minHeight: 76,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  actionIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#F1E9DF',
  },
  actionIconText: {
    color: '#8A6B3F',
    fontSize: 20,
  },
  actionCopy: {
    flex: 1,
  },
  actionLabel: {
    color: '#514438',
    fontSize: 14,
    fontWeight: '700',
  },
  actionDescription: {
    marginTop: 4,
    color: '#8A7A6B',
    fontSize: 12,
  },
  chevron: {
    color: '#B09C89',
    fontSize: 26,
    fontWeight: '300',
  },
  pressed: {
    opacity: 0.65,
  },
  futureRow: {
    minHeight: 76,
    marginTop: 28,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#DDD2C5',
    borderRadius: 16,
    opacity: 0.75,
  },
  futureIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#E9DFD3',
  },
  futureIconText: {
    color: '#9B866F',
    fontSize: 20,
  },
  futureCopy: {
    flex: 1,
  },
  futureTitle: {
    color: '#75695D',
    fontSize: 13,
    fontWeight: '700',
  },
  futureDescription: {
    marginTop: 4,
    color: '#9B8D80',
    fontSize: 12,
    lineHeight: 17,
  },
});
