import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { SafeAreaView } from 'react-native-safe-area-context';
import { analyzeStyle, getDevelopmentUserId } from '../services/api';
import type { RootTabParamList } from '../navigation';

type InspirationNavigation = BottomTabNavigationProp<RootTabParamList>;

export default function InspirationScreen() {
  const navigation = useNavigation<InspirationNavigation>();
  const [images, setImages] = useState<ImagePicker.ImagePickerAsset[]>([]);
  const [flickrUrl, setFlickrUrl] = useState('');
  const [isPicking, setIsPicking] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const trimmedFlickrUrl = flickrUrl.trim();
  const hasFlickrUrl = trimmedFlickrUrl.length > 0;
  const canAnalyze = (hasFlickrUrl || images.length >= 3) && !isAnalyzing;

  const addInspiration = async () => {
    if (isPicking) {
      return;
    }

    setIsPicking(true);
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Photo access needed',
          'Allow photo access in your device settings to add outfit inspiration.',
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsMultipleSelection: true,
        selectionLimit: 20,
        quality: 0.9,
      });

      if (!result.canceled) {
        setImages((currentImages) => {
          const existingUris = new Set(currentImages.map((image) => image.uri));
          const newImages = result.assets.filter((image) => !existingUris.has(image.uri));
          return [...currentImages, ...newImages];
        });
      }
    } finally {
      setIsPicking(false);
    }
  };

  const removeImage = (uri: string) => {
    setImages((currentImages) => currentImages.filter((image) => image.uri !== uri));
  };

  const buildStyleDna = async () => {
    if (!canAnalyze) {
      return;
    }

    setErrorMessage(null);
    setIsAnalyzing(true);
    try {
      const analysis = await analyzeStyle(
        images,
        getDevelopmentUserId(),
        hasFlickrUrl ? [trimmedFlickrUrl] : [],
      );
      navigation.navigate('Style DNA', { analysis });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Style analysis failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.eyebrow}>DISCOVER YOUR STYLE</Text>
        <Text style={styles.title}>Inspiration</Text>
        <Text style={styles.subtitle}>Select outfits you love so we can learn what feels like you.</Text>

        <Text nativeID="flickrUrlLabel" style={styles.inputLabel}>
          Or paste a Flickr URL
        </Text>
        <TextInput
          accessibilityLabel="Flickr inspiration URL"
          accessibilityLabelledBy="flickrUrlLabel"
          autoCapitalize="none"
          autoCorrect={false}
          editable={!isAnalyzing}
          keyboardType="url"
          onChangeText={setFlickrUrl}
          placeholder="https://flic.kr/ps/48aJQy"
          placeholderTextColor="#8D7B6D"
          style={styles.urlInput}
          value={flickrUrl}
        />

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Add inspiration images"
          disabled={isPicking}
          onPress={addInspiration}
          style={({ pressed }) => [styles.addButton, pressed && styles.pressed, isPicking && styles.disabled]}
        >
          <Text style={styles.addButtonIcon}>+</Text>
          <Text style={styles.addButtonText}>{isPicking ? 'Opening photos...' : 'Add inspiration'}</Text>
        </Pressable>

        {images.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>✦</Text>
            <Text style={styles.emptyTitle}>Your inspiration board is empty</Text>
            <Text style={styles.emptyText}>
              Add at least three outfits, or paste a Flickr URL, to start shaping your Style DNA.
            </Text>
          </View>
        ) : (
          <View style={styles.grid}>
            {images.map((image) => (
              <View key={image.uri} style={styles.tile}>
                <Image
                  source={{ uri: image.uri }}
                  style={[styles.image, { aspectRatio: image.width / image.height }]}
                />
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Remove inspiration image"
                  onPress={() => removeImage(image.uri)}
                  style={({ pressed }) => [styles.removeButton, pressed && styles.pressed]}
                >
                  <Text style={styles.removeButtonText}>×</Text>
                </Pressable>
              </View>
            ))}
          </View>
        )}

        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !canAnalyze, busy: isAnalyzing }}
          disabled={!canAnalyze}
          onPress={buildStyleDna}
          style={({ pressed }) => [styles.cta, !canAnalyze && styles.ctaDisabled, pressed && styles.pressed]}
        >
          {isAnalyzing ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={[styles.ctaArrow, !canAnalyze && styles.ctaTextDisabled]}>→</Text>
          )}
          <Text style={[styles.ctaText, !canAnalyze && styles.ctaTextDisabled]}>
            {isAnalyzing ? 'Analyzing your style...' : 'Build My Style DNA'}
          </Text>
        </Pressable>
        {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
        {images.length > 0 && images.length < 3 && !hasFlickrUrl ? (
          <Text style={styles.helperText}>
            Add {3 - images.length} more {3 - images.length === 1 ? 'image' : 'images'} to continue, or paste a Flickr URL.
          </Text>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F7F3EE',
  },
  content: {
    padding: 24,
    paddingBottom: 32,
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
    lineHeight: 25,
  },
  inputLabel: {
    marginTop: 24,
    color: '#2E2925',
    fontSize: 14,
    fontWeight: '700',
  },
  urlInput: {
    minHeight: 52,
    marginTop: 10,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#E4D9CE',
    borderRadius: 14,
    backgroundColor: '#FFFFFF',
    color: '#2E2925',
    fontSize: 16,
  },
  addButton: {
    minHeight: 52,
    marginTop: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 14,
    backgroundColor: '#2E2925',
  },
  addButtonIcon: {
    color: '#F7F3EE',
    fontSize: 24,
    fontWeight: '300',
    lineHeight: 25,
  },
  addButtonText: {
    color: '#F7F3EE',
    fontSize: 16,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.75,
  },
  disabled: {
    opacity: 0.6,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: 32,
    padding: 28,
    borderWidth: 1,
    borderColor: '#E4D9CE',
    borderRadius: 18,
    borderStyle: 'dashed',
  },
  emptyIcon: {
    color: '#A15C38',
    fontSize: 28,
  },
  emptyTitle: {
    marginTop: 12,
    color: '#2E2925',
    fontSize: 17,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptyText: {
    maxWidth: 270,
    marginTop: 8,
    color: '#6E625A',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 24,
  },
  tile: {
    position: 'relative',
    width: '48%',
    overflow: 'hidden',
    borderRadius: 14,
    backgroundColor: '#E8DED5',
  },
  image: {
    width: '100%',
    minHeight: 150,
  },
  removeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    backgroundColor: 'rgba(46, 41, 37, 0.8)',
  },
  removeButtonText: {
    color: '#FFF',
    fontSize: 20,
    fontWeight: '400',
    lineHeight: 23,
  },
  cta: {
    minHeight: 56,
    marginTop: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    borderRadius: 14,
    backgroundColor: '#A15C38',
  },
  ctaDisabled: {
    backgroundColor: '#D8C9BC',
  },
  ctaText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  ctaTextDisabled: {
    color: '#8D7B6D',
  },
  ctaArrow: {
    color: '#FFF',
    fontSize: 22,
  },
  helperText: {
    marginTop: 10,
    color: '#8D7B6D',
    fontSize: 13,
    textAlign: 'center',
  },
  errorText: {
    marginTop: 12,
    color: '#A13F38',
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
});
