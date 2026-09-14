import { useNavigation } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

type RootTabParamList = {
  Inspiration: undefined;
  'Style DNA': undefined;
  Generate: undefined;
  Profile: undefined;
};

type StyleDnaNavigation = BottomTabNavigationProp<RootTabParamList>;

type StyleCategory = {
  name: string;
  percentage: number;
  color: string;
};

type StyleColor = {
  name: string;
  value: string;
  border?: string;
};

const styleCategories: StyleCategory[] = [
  { name: 'Minimalist', percentage: 38, color: '#3F716A' },
  { name: 'Streetwear', percentage: 31, color: '#6B7F7B' },
  { name: 'Smart Casual', percentage: 19, color: '#A15C38' },
  { name: 'Vintage', percentage: 12, color: '#B89B74' },
];

const preferredColors: StyleColor[] = [
  { name: 'Black', value: '#252525' },
  { name: 'White', value: '#FFFFFF', border: '#D9D3CC' },
  { name: 'Beige', value: '#D8C4A8' },
  { name: 'Blue', value: '#66849A' },
];

const styleTraits = ['Neutral palette', 'Relaxed silhouettes', 'Layering', 'Clean sneakers'];

export default function StyleDnaScreen() {
  const navigation = useNavigation<StyleDnaNavigation>();

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>YOUR PROFILE</Text>
        <Text style={styles.title}>Your Style DNA</Text>
        <Text style={styles.subtitle}>
          A snapshot of the fashion preferences that make your style uniquely yours.
        </Text>

        <View style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <View>
              <Text style={styles.cardEyebrow}>STYLE MIX</Text>
              <Text style={styles.cardTitle}>Your signature blend</Text>
            </View>
            <Text style={styles.primaryPercentage}>38%</Text>
          </View>

          <View style={styles.categoryList}>
            {styleCategories.map((category) => (
              <View key={category.name} style={styles.categoryRow}>
                <View style={styles.categoryLabelRow}>
                  <Text style={styles.categoryName}>{category.name}</Text>
                  <Text style={styles.categoryPercentage}>{category.percentage}%</Text>
                </View>
                <View style={styles.progressTrack}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${category.percentage}%`, backgroundColor: category.color },
                    ]}
                  />
                </View>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your color palette</Text>
          <View style={styles.paletteRow}>
            {preferredColors.map((color) => (
              <View key={color.name} style={styles.paletteItem}>
                <View
                  style={[
                    styles.swatch,
                    { backgroundColor: color.value },
                    color.border ? { borderColor: color.border, borderWidth: 1 } : null,
                  ]}
                />
                <Text style={styles.paletteLabel}>{color.name}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key style traits</Text>
          <View style={styles.traitsRow}>
            {styleTraits.map((trait) => (
              <View key={trait} style={styles.traitChip}>
                <Text style={styles.traitMark}>✓</Text>
                <Text style={styles.traitText}>{trait}</Text>
              </View>
            ))}
          </View>
        </View>

        <Text style={styles.context}>Based on 5 inspiration images</Text>

        <Pressable
          accessibilityRole="button"
          onPress={() => navigation.navigate('Generate')}
          style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
        >
          <Text style={styles.ctaText}>Generate an Outfit</Text>
          <Text style={styles.ctaArrow}>→</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#EEF2F1',
  },
  content: {
    padding: 24,
    paddingBottom: 32,
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
    lineHeight: 25,
  },
  summaryCard: {
    marginTop: 24,
    padding: 20,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  cardEyebrow: {
    color: '#6B7F7B',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  cardTitle: {
    marginTop: 6,
    color: '#253331',
    fontSize: 18,
    fontWeight: '700',
  },
  primaryPercentage: {
    color: '#3F716A',
    fontSize: 24,
    fontWeight: '700',
  },
  categoryList: {
    gap: 16,
    marginTop: 24,
  },
  categoryRow: {
    gap: 8,
  },
  categoryLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  categoryName: {
    color: '#394844',
    fontSize: 14,
    fontWeight: '600',
  },
  categoryPercentage: {
    color: '#6B7F7B',
    fontSize: 13,
    fontWeight: '700',
  },
  progressTrack: {
    height: 8,
    overflow: 'hidden',
    borderRadius: 4,
    backgroundColor: '#E7EEEC',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  section: {
    marginTop: 28,
  },
  sectionTitle: {
    color: '#253331',
    fontSize: 18,
    fontWeight: '700',
  },
  paletteRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 18,
    paddingHorizontal: 4,
  },
  paletteItem: {
    alignItems: 'center',
    gap: 8,
  },
  swatch: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  paletteLabel: {
    color: '#5F706D',
    fontSize: 12,
  },
  traitsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 16,
  },
  traitChip: {
    minHeight: 38,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    paddingHorizontal: 13,
    borderRadius: 19,
    backgroundColor: '#DDE9E6',
  },
  traitMark: {
    color: '#3F716A',
    fontSize: 14,
    fontWeight: '700',
  },
  traitText: {
    color: '#39544F',
    fontSize: 13,
    fontWeight: '600',
  },
  context: {
    marginTop: 28,
    color: '#71817D',
    fontSize: 13,
    textAlign: 'center',
  },
  cta: {
    minHeight: 56,
    marginTop: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    borderRadius: 14,
    backgroundColor: '#3F716A',
  },
  ctaText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  ctaArrow: {
    color: '#FFFFFF',
    fontSize: 22,
  },
  pressed: {
    opacity: 0.75,
  },
});
