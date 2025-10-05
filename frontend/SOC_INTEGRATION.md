# SOC Assistant Integration

This integration adds AI-powered Security Operations Center (SOC) capabilities to your NIDS system using Google's Gemini API.

## Features

- **Real-time Attack Analysis**: Analyzes detected attacks and provides immediate response steps
- **Windows-Specific Commands**: Generates PowerShell commands tailored for Windows environments
- **Interactive Popup**: User-friendly interface with actionable buttons for each response step
- **Evidence Collection**: Automatically includes commands for preserving attack evidence
- **Severity Assessment**: Determines attack severity based on type and confidence levels

## Components

### 1. Gemini API Service (`lib/gemini.ts`)
- Handles communication with Google Gemini API
- Formats the SOC prompt with attack data
- Parses and validates API responses
- Includes fallback responses for API failures

### 2. SOC Types (`types/soc.ts`)
- Defines TypeScript interfaces for attack inputs and SOC responses
- Ensures type safety across the integration

### 3. SOC Popup Component (`components/SOCPopup.tsx`)
- Displays the SOC response in an interactive dialog
- Shows attack classification with confidence levels
- Lists prioritized response steps with action buttons
- Copies PowerShell commands to clipboard when buttons are clicked

### 4. SOC Assistant Hook (`hooks/useSOCAssistant.ts`)
- Manages SOC analysis state and operations
- Converts alert data to the required format
- Provides methods for analyzing real attacks and simulating test scenarios

### 5. Test Panel (`components/SOCTestPanel.tsx`)
- Allows testing the SOC integration with simulated attacks
- Provides dropdown menus for selecting attack types and severity levels
- Useful for demonstrations and validation

## Usage

### Testing the Integration
1. Navigate to the Dashboard tab
2. Use the "SOC Assistant Test Panel" at the bottom
3. Select an attack type (DDoS, PortScan, BruteForce, etc.)
4. Choose a severity level (low, medium, high, critical)
5. Click "Simulate Attack & Get SOC Response"

### Real Attack Analysis
The system automatically integrates with your existing classification chart:
1. When attacks are detected, click the "SOC Response" button in the Attack Class Distribution chart
2. The system will analyze the most common attack type from your current data
3. A popup will appear with the AI-generated response plan

### Response Steps
Each SOC response includes:
- **Classification**: Attack type with confidence percentage
- **Prioritized Steps**: Up to 8 immediate actions ranked by importance
- **PowerShell Commands**: Windows-specific commands for each step
- **Time Estimates**: Expected duration for each action
- **Evidence Preservation**: Commands to capture logs and network traffic

## API Configuration

The Gemini API key is currently hardcoded in `lib/gemini.ts`. For production use, consider:
- Moving the API key to environment variables
- Implementing proper key rotation
- Adding rate limiting and error handling

## Security Considerations

- Commands are copied to clipboard for manual execution (not auto-executed)
- All suggested actions are reversible and non-destructive
- Evidence is stored in `C:\ProgramData\SecAssist\evidence\`
- IP addresses are shown in full (not masked) for accurate blocking

## Customization

You can customize the SOC behavior by modifying:
- **Prompt Template**: Edit the `SOC_PROMPT` in `lib/gemini.ts`
- **Severity Logic**: Adjust `determineSeverity()` in `hooks/useSOCAssistant.ts`
- **Evidence Paths**: Update default paths in the prompt template
- **UI Styling**: Modify the popup and button styles in `components/SOCPopup.tsx`

## Troubleshooting

- **API Errors**: Check the browser console for Gemini API error messages
- **Missing Commands**: Ensure the response includes valid PowerShell syntax
- **Popup Not Showing**: Verify the `isPopupOpen` state is being set correctly
- **Toast Notifications**: Make sure Sonner is properly configured in your app

## Future Enhancements

- Integration with real-time alert streams
- Custom response templates for different attack types
- Integration with Windows Event Logs
- Automated evidence collection
- Multi-language support for international teams