import type { CsItemAnalyzeResponse } from './cs';

export type CsHomeHistoryItem = {
  id: string;
  goodId: number;
  itemName: string;
  marketHashName: string;
  platform: string;
  signalScore: number;
  buySignal: string;
  createdAt: string;
  result: CsItemAnalyzeResponse;
};

export type CsSkillInfo = {
  id: string;
  displayName: string;
  description: string;
  category: string;
  source: string;
};
