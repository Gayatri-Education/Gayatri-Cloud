import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SUPPORTED_LANGUAGES, TRANSLATIONS } from '../src/lib/i18n/catalogs';
import { OfflineStorage, OfflineBundle } from '../src/lib/offline/offline-storage';
import { ApiClient } from '../src/lib/api-client';

class LocalStorageMock {
  private store: Record<string, string> = {};
  clear() {
    this.store = {};
  }
  getItem(key: string) {
    return this.store[key] || null;
  }
  setItem(key: string, value: string) {
    this.store[key] = String(value);
  }
  removeItem(key: string) {
    delete this.store[key];
  }
}

describe('P17 Localization, Accessibility & Offline Reading — Frontend Tests', () => {
  let client: ApiClient;
  const mockStorage = new LocalStorageMock();

  beforeEach(() => {
    (global as any).localStorage = mockStorage;
    (global as any).window = global;
    mockStorage.clear();
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Platform Language Registry & Catalogs', () => {
    it('supports exactly 8 verified platform languages with native script labels', () => {
      expect(SUPPORTED_LANGUAGES).toHaveLength(8);
      const codes = SUPPORTED_LANGUAGES.map((l) => l.code);
      expect(codes).toEqual(['en', 'hi', 'sa', 'ta', 'te', 'kn', 'mr', 'bn']);

      const nativeLabels = Object.fromEntries(SUPPORTED_LANGUAGES.map((l) => [l.code, l.nativeLabel]));
      expect(nativeLabels.hi).toBe('हिन्दी');
      expect(nativeLabels.sa).toBe('संस्कृतम्');
      expect(nativeLabels.ta).toBe('தமிழ்');
      expect(nativeLabels.te).toBe('తెలుగు');
      expect(nativeLabels.kn).toBe('ಕನ್ನಡ');
      expect(nativeLabels.mr).toBe('मराठी');
      expect(nativeLabels.bn).toBe('বাংলা');
    });

    it('translates strings across languages and interpolates dynamic arguments', () => {
      // Hindi interpolation
      const hiTemplate = TRANSLATIONS.hi.welcome;
      expect(hiTemplate).toContain('{name}');
      const interpolated = hiTemplate.replace('{name}', 'आकाश');
      expect(interpolated).toBe('पुनः स्वागत है, आकाश');

      // Sanskrit tutoring label
      expect(TRANSLATIONS.sa.tutor).toBe('एआई गुरुः');

      // Tamil courses label
      expect(TRANSLATIONS.ta.courses).toBe('பாடநெறிகள்');

      // Kannada offline guidance
      expect(TRANSLATIONS.kn.offline_library).toBe('ಆಫ್‌ಲೈನ್ ಲೈಬ್ರರಿ');

      // Comprehensive portal navigation & dashboard keys across all 8 languages
      for (const lang of SUPPORTED_LANGUAGES) {
        const dict = TRANSLATIONS[lang.code];
        expect(dict).toBeDefined();
        expect(dict.student_portal_title).toBeTruthy();
        expect(dict.quick_switch).toBeTruthy();
        expect(dict.launch_portal).toBeTruthy();
        expect(dict.your_courses).toBeTruthy();
        expect(dict.browse_catalog).toBeTruthy();
        expect(dict.welcome_back).toContain('{name}');
      }
    });
  });

  describe('2. Offline Course Storage & Staleness Cache', () => {
    const mockBundle: OfflineBundle = {
      course_id: 'crs-101',
      course_title: 'Quantum Physics Fundamentals',
      description: 'Introductory wave mechanics',
      version_id: 'v-101',
      version_tag: 'v1.0.0',
      sha256_checksum: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      packaged_at: new Date().toISOString(),
      lessons_count: 2,
      lessons: [
        {
          chunk_id: 'chk-1',
          title: 'Lesson Section 1',
          content_text: 'Wave-particle duality overview',
          sequence_order: 0,
          token_count: 50,
        },
        {
          chunk_id: 'chk-2',
          title: 'Lesson Section 2',
          content_text: 'Schrödinger wave mechanics',
          sequence_order: 1,
          token_count: 75,
        },
      ],
      offline_guidance: 'Reading mode active. Live AI tutoring and graded exams require reconnection.',
    };

    it('persists and retrieves downloaded course bundles from local storage', () => {
      expect(OfflineStorage.listBundles()).toHaveLength(0);
      expect(OfflineStorage.getBundle('crs-101')).toBeNull();

      OfflineStorage.saveBundle(mockBundle);

      const retrieved = OfflineStorage.getBundle('crs-101');
      expect(retrieved).not.toBeNull();
      expect(retrieved?.course_title).toBe('Quantum Physics Fundamentals');
      expect(retrieved?.lessons).toHaveLength(2);
      expect(retrieved?.sha256_checksum).toHaveLength(64);

      expect(OfflineStorage.listBundles()).toHaveLength(1);

      OfflineStorage.removeBundle('crs-101');
      expect(OfflineStorage.getBundle('crs-101')).toBeNull();
      expect(OfflineStorage.listBundles()).toHaveLength(0);
    });
  });

  describe('3. API Client Localization & Offline Methods', () => {
    it('calls getSupportedLanguages endpoint', async () => {
      const mockLangs = {
        languages: [
          { code: 'en', native_label: 'English', english_name: 'English', script: 'Latin' },
          { code: 'hi', native_label: 'हिन्दी', english_name: 'Hindi', script: 'Devanagari' },
        ],
      };
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockLangs,
      } as any);

      const res = await client.getSupportedLanguages();
      expect(res.languages).toHaveLength(2);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/localization/languages',
        expect.anything()
      );
    });

    it('updates user language preference', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ language_code: 'hi', message: 'Language preference saved.' }),
      } as any);

      const res = await client.updateLanguagePreference('hi');
      expect(res.language_code).toBe('hi');
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/localization/preference',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ language_code: 'hi' }),
        })
      );
    });

    it('checks bundle staleness against online published version', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          course_id: 'crs-101',
          local_version_tag: 'v1.0.0',
          latest_version_tag: 'v2.0.0',
          is_stale: true,
          status: 'stale',
          message: 'Course version v2.0.0 is available online.',
        }),
      } as any);

      const res = await client.checkBundleStaleness('crs-101', 'v1.0.0');
      expect(res.is_stale).toBe(true);
      expect(res.latest_version_tag).toBe('v2.0.0');
    });
  });
});
