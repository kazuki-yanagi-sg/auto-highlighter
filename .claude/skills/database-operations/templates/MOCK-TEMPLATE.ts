// Mock テンプレート
// 参考: client/src/test/models/tickets.ts
// 配置: client/src/test/models/[model-name].ts

import type { Model } from '@prisma/client'

const MOCK_MODELS_COUNT = 10

export const createMockModel = ({
  index = 0,
  ...overrides
}: {
  index?: number
} & Partial<Model> = {}): Model => ({
  id: `model-${index}`,
  createdAt: new Date(2024, 0, index),
  updatedAt: new Date(2024, 0, index),

  title: `Test Model ${index}`,
  description: `Test Description ${index}`,
  status: 'ACTIVE',

  userId: `user-${(index % 3) + 1}`,

  ...overrides,
})

export const mockModel: Model = createMockModel()

export const mockModels: Model[] = Array.from(
  { length: MOCK_MODELS_COUNT },
  (_, i) => createMockModel({ index: i }),
)
