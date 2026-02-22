import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.hasomed.mentalcarepilot',
  appName: 'MentalCarePilot',
  webDir: 'apps/web/dist',
  server: {
    androidScheme: 'https',
  },
};

export default config;
