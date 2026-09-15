import type { AnalyzeResponse } from './services/api';

export type RootTabParamList = {
  Inspiration: undefined;
  'Style DNA': { analysis: AnalyzeResponse } | undefined;
  Generate: undefined;
  Profile: undefined;
};
