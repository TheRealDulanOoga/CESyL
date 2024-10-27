#include "string"

const int GLOBALBITDEPTH = 5;
const int GLOBALPWMSTEPS = pow(2, GLOBALBITDEPTH);
const int MAXYELLOWPCBENCODERS = 11;
const int GLOBALDELAYMICROSECONDS = 5;

int outputLatch = 33;
int outputClock = 34;

int inputLD = 32;
int inputCLK = 31;
int inputCLKINH = 30;

int totalBlackPCBCount = 29;
int totalYellowPCBCount = 6;
int totalEncoderCount = 55;
int totalButtonCount = 6;

// BLACK PCBS
class BlackRegisterModule
{
public:
  int dataPinNumber;
  int LEDCount = 8;
  char PWMSteps = GLOBALPWMSTEPS;
  char BitDepth = GLOBALBITDEPTH;
  char PWMStepsMask;
  short LEDValues[8] = {(short)0b11111'01111'00111, (short)0b00111'11111'01111, (short)0b00111'01111'11111, (short)0b11111'00111'01111,
                        (short)0b01111'11111'00111, (short)0b00111'01111'11111, (short)0b00111'11111'01111, (short)0b11111'01111'00111};

  BlackRegisterModule(int setDataPinNumber)
  {
    dataPinNumber = setDataPinNumber;
  }

  void Initialize()
  {
    pinMode(dataPinNumber, OUTPUT);

    PWMStepsMask = PWMSteps - 1;
  }

  void OutputLEDValues(int PWMIndex, int currentLEDIndex)
  {
    int shiftSize = (currentLEDIndex % 3) * BitDepth; // Get if it is a R, G, or B LED and then calculate shift size using PWM depth

    int activeBitAmount = (LEDValues[currentLEDIndex / 3] >> shiftSize) & PWMStepsMask; // lowkey don't know what this does
    int calculatedPWM = ((int)pow(2, PWMSteps) - 1) >> (PWMSteps - activeBitAmount);    // Find the chunk of data that corresponds to this particular R, G, or B LED
    int currentDisplayedBit = (calculatedPWM >> PWMIndex) & 1;                          // Finds the bit that needs to be shown on this PWM step

    digitalWrite(dataPinNumber, currentDisplayedBit);
  }
};

BlackRegisterModule blackPCBList[] = {
    BlackRegisterModule(6),
    BlackRegisterModule(7),
    BlackRegisterModule(8),
    BlackRegisterModule(9),
    BlackRegisterModule(10),
    BlackRegisterModule(11),
    BlackRegisterModule(12),
    BlackRegisterModule(24),
    BlackRegisterModule(25),
    BlackRegisterModule(26),
    BlackRegisterModule(27),
    BlackRegisterModule(28),
    BlackRegisterModule(29),
    BlackRegisterModule(35),
    BlackRegisterModule(39),
    BlackRegisterModule(40),
    BlackRegisterModule(38),
    BlackRegisterModule(36),
    BlackRegisterModule(37),
    BlackRegisterModule(41),
    BlackRegisterModule(13),
    BlackRegisterModule(14),
    BlackRegisterModule(15),
    BlackRegisterModule(16),
    BlackRegisterModule(17),
    BlackRegisterModule(18),
    BlackRegisterModule(20),
    BlackRegisterModule(22),
    BlackRegisterModule(23)};

// YELLOW PCBS
class YellowRegisterModule
{
public:
  int dataPinNumber;
  int encoderCount;
  int buttonCount = 0;
  long long encoderData = pow(2, 32);

  YellowRegisterModule(int setDataPinNumber, int setEncoderCount)
  {
    dataPinNumber = setDataPinNumber;
    encoderCount = setEncoderCount;
  }
  YellowRegisterModule(int setDataPinNumber, int setEncoderCount, int setButtonCount)
  {
    dataPinNumber = setDataPinNumber;
    encoderCount = setEncoderCount;
    buttonCount = setButtonCount;
  }

  void Initialize()
  {
    pinMode(dataPinNumber, INPUT);
  }
};

YellowRegisterModule yellowPCBList[] = {
    YellowRegisterModule(0, 10),
    YellowRegisterModule(1, 9, 4),
    YellowRegisterModule(2, 10),
    YellowRegisterModule(3, 10),
    YellowRegisterModule(4, 7, 2),
    YellowRegisterModule(5, 9)};

// ALL INPUTS
class InputOutputModule
{
public:
  short indexOFBlackPCB;
  short indexOFYellowPCB;
  short indexONBlackPCB;
  short indexONYellowPCB;

  InputOutputModule(short blackPCBNumber, short yellowPCBNumber, short blackPCBOrder, short yellowPCBOrder)
  {
    indexOFBlackPCB = blackPCBNumber - 1;
    indexOFYellowPCB = yellowPCBNumber - 1;
    indexONBlackPCB = blackPCBOrder - 1;
    indexONYellowPCB = yellowPCBOrder - 1;
  }
};

// ENCODERS
class EncoderModule : public InputOutputModule
{
public:
  int encoderValues = 0b111;
  short LEDValues[4] = {(short)0b11111'11111'00000, (short)0b00000'11111'11111, (short)0b11111'00000'11111, (short)0b11111'11111'11111};

  long rotationValue = 0;
  byte lastGreyCodeValue = 0;
  byte lastBitAdd = 0;

  EncoderModule(short blackPCBNumber, short yellowPCBNumber, short blackPCBOrder, short yellowPCBOrder) : InputOutputModule(blackPCBNumber, yellowPCBNumber, blackPCBOrder, yellowPCBOrder) {};

  void LEDValueAssignments()
  {
    for (int j = 0; j < 4; j++) // transfer LED values from Encoder to Black PCB
    {
      blackPCBList[indexOFBlackPCB].LEDValues[j + 4 - indexONBlackPCB * 4] = LEDValues[3 - j];
    }
  }

  void PrintEncoderValues()
  {
    Serial.print((encoderValues >> 2) & 0b1, BIN);
    Serial.print(".");
    Serial.print(rotationValue);

    Serial.print("|");
  }

  void ConvertFromGreyCode()
  {
    byte currentGreyCodeValue = encoderValues & 0b011;
    byte currentBitAdd = (encoderValues & 0b001) + ((encoderValues & 0b010) >> 1);

    int bitAddDifference = currentBitAdd - lastBitAdd;
    int regularDifference = currentGreyCodeValue - lastGreyCodeValue;
    int lastBitFlipChecker = lastGreyCodeValue * regularDifference;
    int currentBitFlipChecker = currentGreyCodeValue * regularDifference;

    bool rotationShouldBeZero = currentGreyCodeValue == lastGreyCodeValue || bitAddDifference % 2 == 0; // values stayed the same || values skipped a step; error
    bool bitShouldBeFlipped = -lastBitFlipChecker % 5 == 1 || currentBitFlipChecker % 5 == 1;           // Don't ask me why this works. I made a google spreadsheet and looked at it for 30 mins for this lol

    int rotationAdjustment = 0; // default value is zero

    if (bitShouldBeFlipped)
    {
      // correcting for bitAddDifference bits that are opposite to what the rotation value should be
      rotationAdjustment = -bitAddDifference * !rotationShouldBeZero;
    }
    else
    {
      // all other bitAddDifference bits should now be properly aligned with the rotation value:
      rotationAdjustment = bitAddDifference * !rotationShouldBeZero;
    }

    lastBitAdd = currentBitAdd;
    lastGreyCodeValue = currentGreyCodeValue;
    rotationValue += rotationAdjustment;
  }

  bool ParseLEDValuesFromSerial(char LEDValueDivider, char encoderDivider, char endSignal, byte maxDigitCountInValue = GLOBALBITDEPTH + 1)
  {
    std::string completeInt("");
    char currentChar;

    for (int i = 0; i < 4; i++)
    {
      completeInt = "";
      for (int j = 0; j < maxDigitCountInValue; j++)
      {
        currentChar = Serial.read();

        if (currentChar == LEDValueDivider)
        {
          LEDValues[i] = atoi(completeInt.c_str());
          break;
        }
        if (currentChar == encoderDivider)
        {
          LEDValues[i] = atoi(completeInt.c_str());
          return false;
        }
        if (currentChar == endSignal)
        {
          return true;
        }

        completeInt += currentChar;
      }
    }
    return false;
  }
};

// BUTTONS
class ButtonModule : public InputOutputModule
{
public:
  bool isPressed = 1;
  short LEDValue = 0b11111'10000'00000;

  ButtonModule(short blackPCBNumber, short yellowPCBNumber, short blackPCBOrder, short yellowPCBOrder) : InputOutputModule(blackPCBNumber, yellowPCBNumber, blackPCBOrder, yellowPCBOrder) {};

  void LEDValueAssignments()
  {
    blackPCBList[indexOFBlackPCB].LEDValues[7 - indexONBlackPCB] = LEDValue;
  }

  void PrintButtonValue(bool isFinalButton)
  {
    Serial.print(isPressed);

    if (isFinalButton)
    {
      Serial.println();
      return;
    }

    Serial.print("|");
  }

  bool ParseLEDValuesFromSerial(char encoderDivider, char endSignal, byte maxDigitCountInValue = GLOBALBITDEPTH + 1)
  {
    std::string completeInt("");
    char currentChar;

    completeInt = "";
    for (int j = 0; j < maxDigitCountInValue; j++)
    {
      currentChar = Serial.read();

      if (currentChar == encoderDivider)
      {
        LEDValue = atoi(completeInt.c_str());
        return false;
      }
      if (currentChar == endSignal)
      {
        return true;
      }

      completeInt += currentChar;
    }
    return false;
  }
};

EncoderModule encoderList[] = {
    EncoderModule(1, 1, 1, 1),
    EncoderModule(1, 1, 2, 2),
    EncoderModule(2, 1, 1, 3),
    EncoderModule(2, 1, 2, 4),
    EncoderModule(3, 1, 1, 5),
    EncoderModule(3, 1, 2, 6),
    EncoderModule(4, 1, 1, 7),
    EncoderModule(4, 1, 2, 8),
    EncoderModule(5, 1, 1, 9),
    EncoderModule(5, 1, 2, 10),
    EncoderModule(6, 2, 1, 1),
    EncoderModule(7, 3, 1, 1),
    EncoderModule(7, 3, 2, 2),
    EncoderModule(8, 3, 1, 3),
    EncoderModule(8, 3, 2, 4),
    EncoderModule(9, 3, 1, 5),
    EncoderModule(9, 3, 2, 6),
    EncoderModule(10, 2, 1, 2),
    EncoderModule(10, 2, 2, 3),
    EncoderModule(11, 2, 1, 4),
    EncoderModule(11, 2, 2, 5),
    EncoderModule(12, 2, 1, 6),
    EncoderModule(12, 2, 2, 7),
    EncoderModule(13, 3, 1, 7),
    EncoderModule(13, 3, 2, 8),
    EncoderModule(14, 3, 1, 9),
    EncoderModule(14, 3, 2, 10),
    EncoderModule(15, 5, 1, 3),
    EncoderModule(15, 5, 2, 4),
    EncoderModule(16, 5, 1, 1),
    EncoderModule(16, 5, 2, 2),
    EncoderModule(17, 2, 1, 8),
    EncoderModule(17, 2, 2, 9),
    EncoderModule(18, 6, 1, 1),
    EncoderModule(18, 6, 2, 2),
    EncoderModule(19, 6, 1, 3),
    EncoderModule(19, 6, 2, 4),
    EncoderModule(20, 4, 1, 1),
    EncoderModule(20, 4, 2, 2),
    EncoderModule(21, 4, 1, 3),
    EncoderModule(21, 4, 2, 4),
    EncoderModule(22, 5, 1, 5),
    EncoderModule(22, 5, 2, 6),
    EncoderModule(23, 6, 1, 5),
    EncoderModule(23, 6, 2, 6),
    EncoderModule(24, 4, 1, 5),
    EncoderModule(24, 4, 2, 6),
    EncoderModule(25, 4, 1, 7),
    EncoderModule(25, 4, 2, 8),
    EncoderModule(26, 4, 1, 9),
    EncoderModule(26, 4, 2, 10),
    EncoderModule(27, 6, 1, 7),
    EncoderModule(27, 6, 2, 8),
    EncoderModule(28, 6, 2, 9),
    EncoderModule(29, 5, 3, 7),
};

ButtonModule buttonList[] = {
    ButtonModule(6, 11, 5, 28),
    ButtonModule(6, 11, 6, 29),
    ButtonModule(6, 11, 7, 30),
    ButtonModule(6, 11, 8, 31),
    ButtonModule(29, 23, 3, 22),
    ButtonModule(29, 23, 4, 23)};

// - - - - - - - - - - - - - - - - -
// - - - - - MAIN CODE - - - - - - -
// - - - - - - - - - - - - - - - - -

void setup()
{
  for (int i = 0; i < totalBlackPCBCount; i++)
  {
    blackPCBList[i].Initialize();
    digitalWrite(blackPCBList[i].dataPinNumber, 0);
  }

  for (int i = 0; i < totalBlackPCBCount; i++)
  {
    yellowPCBList[i].Initialize();
    digitalWrite(yellowPCBList[i].dataPinNumber, 0);
  }

  pinMode(outputLatch, OUTPUT);
  pinMode(outputClock, OUTPUT);

  pinMode(inputLD, OUTPUT);
  pinMode(inputCLK, OUTPUT);
  pinMode(inputCLKINH, OUTPUT);

  Serial.begin(115200);
}

void LEDOutputLoop(int PWMIndex)
{
  for (int currentLED = 0; currentLED < 24; currentLED++) // for every LED index in each black PCB
  {
    for (int currentPCB = 0; currentPCB < totalBlackPCBCount; currentPCB++) // for every item in the blackPCB list
    {
      blackPCBList[currentPCB].OutputLEDValues(PWMIndex, currentLED);
    }
    digitalWrite(outputClock, 0);
    // delayMicroseconds(GLOBALDELAYMICROSECONDS);
    digitalWrite(outputClock, 1);
  }
  digitalWrite(outputLatch, 0);
  delayMicroseconds(GLOBALDELAYMICROSECONDS);
  digitalWrite(outputLatch, 1);
}

void InputAssignmentLoop()
{
  digitalWrite(inputLD, LOW); // load all inputs into register
  delayMicroseconds(GLOBALDELAYMICROSECONDS);
  digitalWrite(inputLD, HIGH); // allow for the shifting of inputs
  delayMicroseconds(GLOBALDELAYMICROSECONDS);

  digitalWrite(inputCLK, HIGH);   // start clock
  digitalWrite(inputCLKINH, LOW); // enable clock

  // shift in data
  bool maskEnable = 1;
  for (long long mask = pow(2, 31); mask > 0; mask >>= 1)
  {
    if (((int)log2(mask) + 1) % 8 == 0)
    {
      maskEnable = !maskEnable;
    }

    digitalWrite(inputCLK, LOW);

    for (int j = 0; j < totalYellowPCBCount; j++)
    {
      yellowPCBList[j].encoderData |= mask;
      yellowPCBList[j].encoderData -= mask;
      if ((digitalRead(yellowPCBList[j].dataPinNumber) + maskEnable) % 2)
        yellowPCBList[j].encoderData |= mask;
    }
    digitalWrite(inputCLK, HIGH);
  }

  digitalWrite(inputCLKINH, HIGH); // reset and disable clock so that the next loop can begin
}

void EncoderValueAssignments()
{
  for (int i = 0; i < totalEncoderCount; i++)
  { // for every encoder in encoder list
    // transfer encoder values from Yellow PCB to Encoder
    EncoderModule enc = encoderList[i];
    encoderList[i].encoderValues = (yellowPCBList[enc.indexOFYellowPCB].encoderData >> ((10 - enc.indexONYellowPCB) * 3 - 1)) & 0b111;
    encoderList[i].ConvertFromGreyCode();
  }

  for (int i = 0; i < 6; i++)
  {
    if (i < 4)
      buttonList[i].isPressed = !((yellowPCBList[1].encoderData >> (i + 1)) & 1);
    else
      buttonList[i].isPressed = !((yellowPCBList[4].encoderData >> (i + 6)) & 1);
  }
}

void loop()
{
  for (int i = 0; i < GLOBALPWMSTEPS; i++) // for every step in the PWM depth
  {
    LEDOutputLoop(i);
    InputAssignmentLoop();
    EncoderValueAssignments();
  }

  if (Serial.available() > 0)
  {
    int buttonIndex = 0;
    bool isFinalInput = 0;
    for (int i = 0; i < totalEncoderCount; i++)
    {
      encoderList[i].PrintEncoderValues();
      encoderList[i].ParseLEDValuesFromSerial('.', '|', '\n');
      encoderList[i].LEDValueAssignments();
    }
    for (int i = 0; i < totalButtonCount; i++)
    {
      isFinalInput = i == totalButtonCount - 1;
      buttonIndex = i;
      if (i < 4)
        buttonIndex = 3 - i;
      buttonList[buttonIndex].PrintButtonValue(isFinalInput);
      buttonList[i].ParseLEDValuesFromSerial('|', '\n');
      buttonList[i].LEDValueAssignments();
    }
  }

  // for (int i = 0; i < totalYellowPCBCount; i++)
  // {
  //   Serial.print(yellowPCBList[i].encoderData, BIN);
  //   Serial.print("|");
  // }
  // Serial.println();
  // for (int i = 0; i < totalEncoderCount; i++)
  // {
  //   Serial.print(encodersList[i].rotationValue);
  //   Serial.print(".");
  //   Serial.print(encodersList[i].encoderValues >> 2 & 0b1, BIN);
  //   Serial.print("|");
  // }
  // Serial.println();
}