import { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  generateOutfit,
  getDevelopmentUserId,
  submitFeedback,
} from '../services/api';
import type { FeedbackReaction, GenerateResponse, RecommendationItem } from '../services/api';

type Occasion = 'College' | 'Casual' | 'Date' | 'Interview' | 'Party';

type FeedbackUiState = {
  selected?: FeedbackReaction;
  status: 'idle' | 'submitting' | 'saved' | 'error';
  error?: string;
};

const occasions: Occasion[] = ['College', 'Casual', 'Date', 'Interview', 'Party'];

const feedbackOptions: { label: string; value: FeedbackReaction }[] = [
  { label: 'Like', value: 'like' },
  { label: 'Maybe', value: 'maybe' },
  { label: 'Not for me', value: 'dislike' },
];

export default function GenerateScreen() {
  const [selectedOccasion, setSelectedOccasion] = useState<Occasion | null>(null);
  const [recommendation, setRecommendation] = useState<GenerateResponse | null>(null);
  const [feedbackByResult, setFeedbackByResult] = useState<Record<number, FeedbackUiState>>({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const requestOutfit = async () => {
    if (!selectedOccasion || isGenerating) {
      return;
    }

    setErrorMessage(null);
    setRecommendation(null);
    setFeedbackByResult({});
    setIsGenerating(true);
    try {
      const response = await generateOutfit(selectedOccasion, getDevelopmentUserId());
      setRecommendation(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Outfit generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  const sendFeedback = async (item: RecommendationItem, reaction: FeedbackReaction) => {
    if (!recommendation) {
      return;
    }

    const current = feedbackByResult[item.id];
    if (current?.status === 'submitting' || current?.status === 'saved') {
      return;
    }

    setFeedbackByResult((previous) => ({
      ...previous,
      [item.id]: { selected: reaction, status: 'submitting' },
    }));

    try {
      await submitFeedback(recommendation.id, item.id, reaction);
      setFeedbackByResult((previous) => ({
        ...previous,
        [item.id]: { selected: reaction, status: 'saved' },
      }));
    } catch (error) {
      setFeedbackByResult((previous) => ({
        ...previous,
        [item.id]: {
          selected: reaction,
          status: 'error',
          error: error instanceof Error ? error.message : 'Could not save feedback.',
        },
      }));
    }
  };

  const canGenerate = Boolean(selectedOccasion) && !isGenerating;

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
          accessibilityState={{ disabled: !canGenerate, busy: isGenerating }}
          disabled={!canGenerate}
          onPress={requestOutfit}
          style={({ pressed }) => [
            styles.generateButton,
            !canGenerate && styles.generateButtonDisabled,
            pressed && styles.pressed,
          ]}
        >
          {isGenerating ? <ActivityIndicator color="#FFFFFF" /> : null}
          <Text style={[styles.generateButtonText, !canGenerate && styles.disabledText]}>
            {isGenerating ? 'Generating...' : 'Generate Outfit'}
          </Text>
          {!isGenerating ? (
            <Text style={[styles.generateArrow, !selectedOccasion && styles.disabledText]}>→</Text>
          ) : null}
        </Pressable>
        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

        {!recommendation ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>✦</Text>
            <Text style={styles.emptyTitle}>Your next look starts here</Text>
            <Text style={styles.emptyText}>
              Pick an occasion above and we will create a look that feels like you.
            </Text>
          </View>
        ) : (
          <View style={styles.results}>
            <Text style={styles.resultEyebrow}>{recommendation.occasion.toUpperCase()} LOOKS</Text>
            {recommendation.provider_status !== 'ok' ? (
              <Text style={styles.providerStatus}>
                Provider status: {recommendation.provider_status}
              </Text>
            ) : null}
            {recommendation.recommendations.length === 0 ? (
              <Text style={styles.explanation}>
                No recommendations were returned. Provider status: {recommendation.provider_status}.
              </Text>
            ) : (
              recommendation.recommendations.map((item) => (
                <RecommendationCard
                  key={item.id}
                  item={item}
                  feedback={feedbackByResult[item.id]}
                  onReact={(reaction) => void sendFeedback(item, reaction)}
                />
              ))
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function RecommendationCard({
  item,
  feedback,
  onReact,
}: {
  item: RecommendationItem;
  feedback?: FeedbackUiState;
  onReact: (reaction: FeedbackReaction) => void;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const isSubmitting = feedback?.status === 'submitting';
  const isSaved = feedback?.status === 'saved';

  const openSource = async () => {
    if (!item.pinterest_url) {
      return;
    }
    try {
      await Linking.openURL(item.pinterest_url);
    } catch {
      // Linking failures stay on the card; feedback UI is independent.
    }
  };

  return (
    <View style={styles.resultCard}>
      {imageFailed || !item.image_url ? (
        <View style={styles.imageFallback}>
          <Text style={styles.imageFallbackText}>Image unavailable</Text>
        </View>
      ) : (
        <Image
          source={{ uri: item.image_url }}
          style={styles.cardImage}
          resizeMode="cover"
          onError={() => setImageFailed(true)}
        />
      )}

      <View style={styles.cardBody}>
        <View style={styles.resultHeader}>
          <Text style={styles.resultTitle}>{item.title || 'Untitled look'}</Text>
          <View style={styles.matchBadge}>
            <Text style={styles.matchValue}>{item.match_score}%</Text>
            <Text style={styles.matchLabel}>match</Text>
          </View>
        </View>

        {item.description ? <Text style={styles.pieceDescription}>{item.description}</Text> : null}
        <Text style={styles.explanation}>{item.match_reason}</Text>

        {item.pinterest_url ? (
          <Pressable
            accessibilityRole="link"
            onPress={() => void openSource()}
            style={({ pressed }) => [styles.sourceButton, pressed && styles.pressed]}
          >
            <Text style={styles.sourceButtonText}>View source</Text>
          </Pressable>
        ) : null}

        <View style={styles.reactionDivider} />
        <Text style={styles.reactionTitle}>How does this feel?</Text>
        <View style={styles.reactionRow}>
          {feedbackOptions.map((option) => {
            const isSelected = feedback?.selected === option.value;
            const disabled = isSubmitting || isSaved;
            return (
              <Pressable
                key={option.value}
                accessibilityRole="button"
                accessibilityState={{ selected: isSelected, disabled }}
                disabled={disabled}
                onPress={() => onReact(option.value)}
                style={({ pressed }) => [
                  styles.reactionButton,
                  isSelected && styles.reactionButtonSelected,
                  disabled && styles.reactionDisabled,
                  pressed && styles.pressed,
                ]}
              >
                <Text style={[styles.reactionText, isSelected && styles.reactionTextSelected]}>
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
        {isSubmitting ? <Text style={styles.feedback}>Saving your reaction...</Text> : null}
        {isSaved ? <Text style={styles.feedback}>Saved. We’ll use this to improve future looks.</Text> : null}
        {feedback?.status === 'error' ? (
          <Text style={styles.feedbackError}>{feedback.error ?? 'Could not save feedback.'}</Text>
        ) : null}
      </View>
    </View>
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
  results: {
    marginTop: 28,
    gap: 16,
  },
  resultCard: {
    overflow: 'hidden',
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
  },
  cardImage: {
    width: '100%',
    height: 240,
    backgroundColor: '#EEE8F1',
  },
  imageFallback: {
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EEE8F1',
  },
  imageFallbackText: {
    color: '#8A7894',
    fontSize: 13,
    fontWeight: '600',
  },
  cardBody: {
    padding: 20,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  resultEyebrow: {
    color: '#8A7894',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  resultTitle: {
    flex: 1,
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
  pieceDescription: {
    marginTop: 12,
    color: '#6E6574',
    fontSize: 14,
    lineHeight: 20,
  },
  explanation: {
    marginTop: 12,
    color: '#6E6574',
    fontSize: 14,
    lineHeight: 21,
  },
  providerStatus: {
    color: '#8A7894',
    fontSize: 13,
  },
  sourceButton: {
    alignSelf: 'flex-start',
    minHeight: 36,
    marginTop: 14,
    justifyContent: 'center',
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: '#EEE8F1',
  },
  sourceButtonText: {
    color: '#6D5680',
    fontSize: 13,
    fontWeight: '700',
  },
  errorText: {
    marginTop: 12,
    color: '#A13F38',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
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
  reactionDisabled: {
    opacity: 0.7,
  },
  reactionText: {
    color: '#6E6574',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
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
  feedbackError: {
    marginTop: 14,
    color: '#A13F38',
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },
});
