import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

type Occasion = 'College' | 'Casual' | 'Date' | 'Interview' | 'Party';
type Reaction = 'Not for me' | 'Like' | 'Love it';

type OutfitRecommendation = {
  occasion: Occasion;
  styleMatch: number;
  explanation: string;
  pieces: string[];
};

const occasions: Occasion[] = ['College', 'Casual', 'Date', 'Interview', 'Party'];

const mockRecommendation: OutfitRecommendation = {
  occasion: 'Casual',
  styleMatch: 92,
  explanation:
    'Matches your neutral palette, relaxed silhouettes, and minimalist streetwear preferences.',
  pieces: [
    'Black oversized tee',
    'Beige relaxed trousers',
    'White sneakers',
    'Silver accessories',
  ],
};

export default function GenerateScreen() {
  const [selectedOccasion, setSelectedOccasion] = useState<Occasion | null>(null);
  const [recommendation, setRecommendation] = useState<OutfitRecommendation | null>(null);
  const [reaction, setReaction] = useState<Reaction | null>(null);

  const generateOutfit = () => {
    if (!selectedOccasion) {
      return;
    }

    setRecommendation({ ...mockRecommendation, occasion: selectedOccasion });
    setReaction(null);
  };

  const selectReaction = (nextReaction: Reaction) => {
    setReaction(nextReaction);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>CREATE YOUR LOOK</Text>
        <Text style={styles.title}>Generate Outfit</Text>
        <Text style={styles.subtitle}>
          Choose an occasion and get a recommendation shaped by your Style DNA.
        </Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What are you dressing for?</Text>
          <View style={styles.occasionGrid}>
            {occasions.map((occasion) => {
              const isSelected = selectedOccasion === occasion;
              return (
                <Pressable
                  key={occasion}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                  onPress={() => setSelectedOccasion(occasion)}
                  style={({ pressed }) => [
                    styles.occasionButton,
                    isSelected && styles.occasionButtonSelected,
                    pressed && styles.pressed,
                  ]}
                >
                  <Text style={[styles.occasionText, isSelected && styles.occasionTextSelected]}>
                    {occasion}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !selectedOccasion }}
          disabled={!selectedOccasion}
          onPress={generateOutfit}
          style={({ pressed }) => [
            styles.generateButton,
            !selectedOccasion && styles.generateButtonDisabled,
            pressed && styles.pressed,
          ]}
        >
          <Text style={[styles.generateButtonText, !selectedOccasion && styles.disabledText]}>
            Generate Outfit
          </Text>
          <Text style={[styles.generateArrow, !selectedOccasion && styles.disabledText]}>→</Text>
        </Pressable>

        {!recommendation ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>✦</Text>
            <Text style={styles.emptyTitle}>Your next look starts here</Text>
            <Text style={styles.emptyText}>
              Pick an occasion above and we will create a look that feels like you.
            </Text>
          </View>
        ) : (
          <View style={styles.resultCard}>
            <View style={styles.resultHeader}>
              <View>
                <Text style={styles.resultEyebrow}>{recommendation.occasion.toUpperCase()} LOOK</Text>
                <Text style={styles.resultTitle}>A look for your day</Text>
              </View>
              <View style={styles.matchBadge}>
                <Text style={styles.matchValue}>{recommendation.styleMatch}%</Text>
                <Text style={styles.matchLabel}>match</Text>
              </View>
            </View>

            <View style={styles.pieceList}>
              {recommendation.pieces.map((piece, index) => (
                <View key={piece} style={styles.pieceRow}>
                  <View style={styles.pieceNumber}>
                    <Text style={styles.pieceNumberText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.pieceText}>{piece}</Text>
                </View>
              ))}
            </View>

            <Text style={styles.explanation}>{recommendation.explanation}</Text>

            <View style={styles.reactionDivider} />
            <Text style={styles.reactionTitle}>How does this feel?</Text>
            <View style={styles.reactionRow}>
              {(['Not for me', 'Like', 'Love it'] as Reaction[]).map((option) => {
                const isSelected = reaction === option;
                return (
                  <Pressable
                    key={option}
                    accessibilityRole="button"
                    accessibilityState={{ selected: isSelected }}
                    onPress={() => selectReaction(option)}
                    style={({ pressed }) => [
                      styles.reactionButton,
                      isSelected && styles.reactionButtonSelected,
                      pressed && styles.pressed,
                    ]}
                  >
                    <Text style={[styles.reactionText, isSelected && styles.reactionTextSelected]}>
                      {option}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
            {reaction ? (
              <Text style={styles.feedback}>We’ll use this to improve future recommendations.</Text>
            ) : null}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F2F0F5',
  },
  content: {
    padding: 24,
    paddingBottom: 32,
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
    lineHeight: 25,
  },
  section: {
    marginTop: 28,
  },
  sectionTitle: {
    color: '#312B37',
    fontSize: 18,
    fontWeight: '700',
  },
  occasionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 16,
  },
  occasionButton: {
    minHeight: 42,
    justifyContent: 'center',
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#D9D0DE',
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
  },
  occasionButtonSelected: {
    borderColor: '#6D5680',
    backgroundColor: '#6D5680',
  },
  occasionText: {
    color: '#6E6574',
    fontSize: 14,
    fontWeight: '600',
  },
  occasionTextSelected: {
    color: '#FFFFFF',
  },
  generateButton: {
    minHeight: 56,
    marginTop: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    borderRadius: 14,
    backgroundColor: '#6D5680',
  },
  generateButtonDisabled: {
    backgroundColor: '#D8D1DA',
  },
  generateButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  generateArrow: {
    color: '#FFFFFF',
    fontSize: 22,
  },
  disabledText: {
    color: '#918896',
  },
  pressed: {
    opacity: 0.75,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: 32,
    padding: 28,
    borderWidth: 1,
    borderColor: '#DDD4E1',
    borderRadius: 18,
    borderStyle: 'dashed',
  },
  emptyIcon: {
    color: '#6D5680',
    fontSize: 28,
  },
  emptyTitle: {
    marginTop: 12,
    color: '#312B37',
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyText: {
    maxWidth: 270,
    marginTop: 8,
    color: '#6E6574',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  resultCard: {
    marginTop: 28,
    padding: 20,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  resultEyebrow: {
    color: '#8A7894',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  resultTitle: {
    marginTop: 6,
    color: '#312B37',
    fontSize: 20,
    fontWeight: '700',
  },
  matchBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#EEE8F1',
  },
  matchValue: {
    color: '#6D5680',
    fontSize: 20,
    fontWeight: '700',
  },
  matchLabel: {
    color: '#8A7894',
    fontSize: 11,
  },
  pieceList: {
    gap: 14,
    marginTop: 24,
  },
  pieceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  pieceNumber: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#F2F0F5',
  },
  pieceNumberText: {
    color: '#6D5680',
    fontSize: 13,
    fontWeight: '700',
  },
  pieceText: {
    color: '#49404E',
    fontSize: 15,
    fontWeight: '600',
  },
  explanation: {
    marginTop: 22,
    color: '#6E6574',
    fontSize: 14,
    lineHeight: 21,
  },
  reactionDivider: {
    height: 1,
    marginTop: 22,
    backgroundColor: '#EAE5EC',
  },
  reactionTitle: {
    marginTop: 18,
    color: '#312B37',
    fontSize: 15,
    fontWeight: '700',
  },
  reactionRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  reactionButton: {
    flex: 1,
    minHeight: 40,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#DDD4E1',
    borderRadius: 10,
  },
  reactionButtonSelected: {
    borderColor: '#6D5680',
    backgroundColor: '#EEE8F1',
  },
  reactionText: {
    color: '#6E6574',
    fontSize: 12,
    fontWeight: '600',
  },
  reactionTextSelected: {
    color: '#6D5680',
  },
  feedback: {
    marginTop: 14,
    color: '#6D5680',
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },
});
