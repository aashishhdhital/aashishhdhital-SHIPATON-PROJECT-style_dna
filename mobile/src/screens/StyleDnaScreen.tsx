import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation, useRoute } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { RouteProp } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { RootTabParamList } from '../navigation';
import { getDevelopmentUserId, getProfile, isMissingProfileError } from '../services/api';
import type { StyleDna } from '../services/api';

type StyleDnaNavigation = BottomTabNavigationProp<RootTabParamList>;

const categoryColors = ['#3F716A', '#6B7F7B', '#A15C38', '#B89B74'];
const colorValues: Record<string, string> = {
  black: '#252525',
  white: '#FFFFFF',
  cream: '#F3EBDD',
  beige: '#D8C4A8',
  gray: '#8D9695',
  grey: '#8D9695',
  blue: '#66849A',
  navy: '#2C3E50',
  brown: '#8B5E3C',
  green: '#4F7A62',
  red: '#A13F38',
  pink: '#D4A5A5',
  tan: '#C8B08A',
};

export default function StyleDnaScreen() {
  const navigation = useNavigation<StyleDnaNavigation>();
  const route = useRoute<RouteProp<RootTabParamList, 'Style DNA'>>();
  const analysis = route.params?.analysis;

  const [styleDna, setStyleDna] = useState<StyleDna | null>(analysis?.style_dna ?? null);
  const [sourcesProcessed, setSourcesProcessed] = useState<number | null>(
    analysis?.sources_processed ?? null,
  );
  const [isLoading, setIsLoading] = useState(!analysis?.style_dna);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasNoProfile, setHasNoProfile] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (analysis?.style_dna) {
        setStyleDna(analysis.style_dna);
        setSourcesProcessed(analysis.sources_processed);
        setHasNoProfile(false);
        setErrorMessage(null);
        setIsLoading(false);
        return;
      }

      let cancelled = false;

      const loadProfile = async () => {
        setIsLoading(true);
        setErrorMessage(null);
        try {
          const profile = await getProfile(getDevelopmentUserId());
          if (cancelled) {
            return;
          }
          setStyleDna(profile.style_dna);
          setSourcesProcessed(null);
          setHasNoProfile(false);
        } catch (error) {
          if (cancelled) {
            return;
          }
          setStyleDna(null);
          if (isMissingProfileError(error)) {
            setHasNoProfile(true);
            setErrorMessage(null);
          } else {
            setHasNoProfile(false);
            setErrorMessage(error instanceof Error ? error.message : 'Could not load Style DNA.');
          }
        } finally {
          if (!cancelled) {
            setIsLoading(false);
          }
        }
      };

      void loadProfile();
      return () => {
        cancelled = true;
      };
    }, [analysis]),
  );

  if (isLoading) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View style={styles.emptyState}>
          <ActivityIndicator color="#3F716A" size="large" />
          <Text style={[styles.subtitle, styles.emptySubtitle]}>Loading your Style DNA...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (errorMessage) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View style={styles.emptyState}>
          <Text style={styles.title}>Your Style DNA</Text>
          <Text style={styles.errorText}>{errorMessage}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => navigation.navigate('Inspiration')}
            style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
          >
            <Text style={styles.ctaText}>Go to Inspiration</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  if (!styleDna || hasNoProfile) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <View style={styles.emptyState}>
          <Text style={styles.title}>Your Style DNA</Text>
          <Text style={[styles.subtitle, styles.emptySubtitle]}>
            Build your Style DNA from inspiration images or a Flickr URL to see your profile here.
          </Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => navigation.navigate('Inspiration')}
            style={({ pressed }) => [styles.cta, pressed && styles.pressed]}
          >
            <Text style={styles.ctaText}>Add inspiration</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

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
            <Text style={styles.primaryPercentage}>{styleDna.styles[0]?.score ?? 0}%</Text>
          </View>

          <View style={styles.categoryList}>
            {styleDna.styles.length === 0 ? (
              <Text style={styles.detailText}>No style mix reported yet.</Text>
            ) : (
              styleDna.styles.map((category, index) => (
                <View key={`${category.name}-${index}`} style={styles.categoryRow}>
                  <View style={styles.categoryLabelRow}>
                    <Text style={styles.categoryName}>{formatLabel(category.name)}</Text>
                    <Text style={styles.categoryPercentage}>{category.score}%</Text>
                  </View>
                  <View style={styles.progressTrack}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${Math.max(0, Math.min(category.score, 100))}%`,
                          backgroundColor: categoryColors[index % categoryColors.length],
                        },
                      ]}
                    />
                  </View>
                </View>
              ))
            )}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your color palette</Text>
          <View style={styles.paletteRow}>
            {styleDna.colors.length === 0 ? (
              <Text style={styles.detailText}>None reported</Text>
            ) : (
              styleDna.colors.map((color) => (
                <View key={color} style={styles.paletteItem}>
                  <View
                    style={[
                      styles.swatch,
                      { backgroundColor: colorValues[color.toLowerCase()] ?? '#C8C8C8' },
                      color.toLowerCase() === 'white' ? { borderColor: '#D9D3CC', borderWidth: 1 } : null,
                    ]}
                  />
                  <Text style={styles.paletteLabel}>{formatLabel(color)}</Text>
                </View>
              ))
            )}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key style traits</Text>
          <View style={styles.traitsRow}>
            {styleDna.traits.length === 0 ? (
              <Text style={styles.detailText}>None reported</Text>
            ) : (
              styleDna.traits.map((trait) => (
                <View key={trait} style={styles.traitChip}>
                  <Text style={styles.traitMark}>✓</Text>
                  <Text style={styles.traitText}>{formatLabel(trait)}</Text>
                </View>
              ))
            )}
          </View>
        </View>

        {sourcesProcessed != null ? (
          <Text style={styles.context}>Based on {sourcesProcessed} inspiration sources</Text>
        ) : (
          <Text style={styles.context}>Loaded from your latest saved profile</Text>
        )}

        <View style={styles.details}>
          <Text style={styles.detailText}>Garments: {formatList(styleDna.garments)}</Text>
          <Text style={styles.detailText}>Fits: {formatList(styleDna.fits)}</Text>
          <Text style={styles.detailText}>Patterns: {formatList(styleDna.patterns)}</Text>
          <Text style={styles.detailText}>Materials: {formatList(styleDna.materials)}</Text>
        </View>

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

function formatLabel(value: string): string {
  return value.replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatList(values: string[]): string {
  return values.length > 0 ? values.map(formatLabel).join(', ') : 'None reported';
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
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    gap: 16,
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
  details: {
    gap: 6,
    marginTop: 14,
  },
  detailText: {
    color: '#5F706D',
    fontSize: 13,
    lineHeight: 19,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 8,
  },
  emptySubtitle: {
    textAlign: 'center',
  },
  errorText: {
    marginTop: 12,
    color: '#A13F38',
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
  cta: {
    minHeight: 56,
    marginTop: 14,
    paddingHorizontal: 18,
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
