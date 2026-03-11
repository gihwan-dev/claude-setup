import type { Meta, StoryObj } from '@storybook/react';
import { ComponentName } from '@/path/to/component';

const meta: Meta<typeof ComponentName> = {
  title: 'Screenshots/Layer/ComponentName',
  component: ComponentName,
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => <Story />,
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div style={{ width: '384px' }}>
      <ComponentName />
    </div>
  ),
};
