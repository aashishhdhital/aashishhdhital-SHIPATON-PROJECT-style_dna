import { useCallback, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  getApiBaseUrl,
  getDevelopmentUserId,
  getHealth,
  getProfile,
  isMissingProfileError,
} from '../services/api';
import type { ProfileResponse } from '../services/api';

function formatLabel(value: string): string {
  return value.replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function ProfileScreen() {
  const [connectionState, setConnectionState] = useState<'loading' | 'connected' | 'error'>('loading');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [profileState, setProfileState] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading');
  const [profileError, setProfileError] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [apiBaseUrl, setApiBaseUrl] = useState<string | null>(null);

  const load = useCallback(async () => {
    setConnectionState('loading');
    setProfileState('loading');
    setConnectionError(null);
    setProfileError(null);

    try {
      setApiBaseUrl(getApiBaseUrl());
      setUserId(getDevelopmentUserId());
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Missing mobile environment configuration.';
      setConnectionState('error');
      setConnectionError(message);
      setProfileState('error');
      setProfileError(message);
      setProfile(null);
      return;
    }

    try {
      await getHealth();
      setConnectionState('connected');
    } catch (error) {
      setConnectionState('error');
      setConnectionError(error instanceof Error ? error.message : 'Unable to reach StyleDNA API');
    }

    try {
      const nextProfile = await getProfile(getDevelopmentUserId());
      setProfile(nextProfile);
      setProfileState('ready');
    } catch (error) {
      setProfile(null);
      if (isMissingProfileError(error)) {
        setProfileState('empty');
        setProfileError(null);
      } else {
        setProfileState('error');
        setProfileError(error instanceof Error ? error.message : 'Could not load profile.');
      }
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  const topStyle = profile?.style_dna.styles[0];
  const secondaryStyle = profile?.style_dna.styles[1];
  const initials = (profile?.name ?? 'SD')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('') || 'SD';

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>ACCOUNT</Text>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.subtitle}>Backend connection and your latest Style DNA.</Text>

        <View style={styles.connectionCard}>
          <View style={styles.connectionCopy}>
            <Text style={styles.connectionLabel}>Backend connection</Text>
            <Text style={styles.connectionStatus}>
              {connectionState === 'loading'
                ? 'Checking StyleDNA API...'
                : connectionState === 'connected'
                  ? 'Connected to StyleDNA API'
                  : connectionError ?? 'Unable to reach StyleDNA API'}
            </Text>
            {apiBaseUrl ? <Text style={styles.connectionMeta}>{apiBaseUrl}</Text> : null}
          </View>
          {connectionState === 'error' ? (
            <Pressable
              accessibilityRole="button"
              onPress={() => void load()}
              style={({ pressed }) => [styles.retryButton, pressed && styles.pressed]}
            >
              <Text style={styles.retryText}>Retry</Text>
            </Pressable>
          ) : (
            <View
              style={[
                styles.connectionDot,
                connectionState === 'loading' && styles.connectionDotLoading,
              ]}
            />
          )}
        </View>

        <View style={styles.userCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <View style={styles.userCopy}>
            <Text style={styles.userName}>{profile?.name ?? 'Development user'}</Text>
            <Text style={styles.userEmail}>
              {userId != null ? `User ID ${userId}` : 'Set EXPO_PUBLIC_DEV_USER_ID'}
            </Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your style at a glance</Text>
          <View style={styles.summaryCard}>
            {profileState === 'loading' ? (
              <View style={styles.centeredRow}>
                <ActivityIndicator color="#8A6B3F" />
                <Text style={styles.summaryLabel}>Loading latest Style DNA...</Text>
              </View>
            ) : null}
            {profileState === 'empty' ? (
              <Text style={styles.emptyCopy}>
                No Style DNA yet. Analyze inspiration first to create a profile.
              </Text>
            ) : null}
            {profileState === 'error' ? (
              <Text style={styles.errorText}>{profileError}</Text>
            ) : null}
            {profileState === 'ready' && profile ? (
              <>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Top style</Text>
                  <Text style={styles.summaryValue}>
                    {topStyle ? `${formatLabel(topStyle.name)} (${topStyle.score}%)` : 'None reported'}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Secondary style</Text>
                  <Text style={styles.summaryValue}>
                    {secondaryStyle
                      ? `${formatLabel(secondaryStyle.name)} (${secondaryStyle.score}%)`
                      : 'None reported'}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Colors</Text>
                  <Text style={styles.summaryValue}>
                    {profile.style_dna.colors.length > 0
                      ? profile.style_dna.colors.map(formatLabel).join(', ')
                      : 'None reported'}
                  </Text>
                </View>
                <View style={[styles.summaryRow, styles.lastRow]}>
                  <Text style={styles.summaryLabel}>Traits</Text>
                  <Text style={styles.summaryValue}>
                    {profile.style_dna.traits.length > 0
                      ? profile.style_dna.traits.map(formatLabel).join(', ')
                      : 'None reported'}
                  </Text>
                </View>
              </>
            ) : null}
          </View>
        </View>

        <View style={styles.futureRow}>
          <View style={styles.futureIcon}>
            <Text style={styles.futureIconText}>◌</Text>
          </View>
          <View style={styles.futureCopy}>
            <Text style={styles.futureTitle}>Hackathon demo account</Text>
            <Text style={styles.futureDescription}>
              This build uses EXPO_PUBLIC_DEV_USER_ID. Sign-in is not implemented.
            </Text>
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
  connectionCard: {
    minHeight: 66,
    marginTop: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#DDD2C5',
    borderRadius: 14,
    backgroundColor: '#FBF8F3',
  },
  connectionCopy: {
    flex: 1,
  },
  connectionLabel: {
    color: '#514438',
    fontSize: 14,
    fontWeight: '700',
  },
  connectionStatus: {
    marginTop: 4,
    color: '#8A7A6B',
    fontSize: 12,
  },
  connectionMeta: {
    marginTop: 4,
    color: '#A08A74',
    fontSize: 11,
  },
  connectionDot: {
    width: 12,
    height: 12,
    marginLeft: 12,
    borderRadius: 6,
    backgroundColor: '#3F716A',
  },
  connectionDotLoading: {
    backgroundColor: '#D8B45D',
  },
  retryButton: {
    minWidth: 58,
    minHeight: 34,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 12,
    borderRadius: 9,
    backgroundColor: '#8A6B3F',
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
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
    flex: 1,
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
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
  },
  summaryRow: {
    minHeight: 51,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE8E0',
  },
  lastRow: {
    borderBottomWidth: 0,
  },
  summaryLabel: {
    color: '#75695D',
    fontSize: 14,
    flexShrink: 0,
  },
  summaryValue: {
    color: '#514438',
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
    textAlign: 'right',
  },
  centeredRow: {
    minHeight: 64,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  emptyCopy: {
    paddingVertical: 16,
    color: '#75695D',
    fontSize: 14,
    lineHeight: 20,
  },
  errorText: {
    paddingVertical: 16,
    color: '#A13F38',
    fontSize: 14,
    lineHeight: 20,
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
