// int LEDValues = 0b1111;
// int encoderValues = 0b1111;

// int inputData = 0;
// int inputShiftLoad = 32;
// int inputCLK = 31;
// int inputCLKInhibit = 30;

#include "string"

int inputButton1 = 30;
int inputDT1 = 31;
int inputSW1 = 32;

int inputButton2 = 27;
int inputDT2 = 28;
int inputSW2 = 29;

int outputData = 24;
int outputLatch = 25;
int outputClock = 26;

char PWMDepth = 8;
char PWMDepthMask = PWMDepth - 1;
short outputDataValues[] = {
    (short)0b111'001'000, (short)0b111'011'000, (short)0b011'111'000, (short)0b001'111'001,
    (short)0b000'111'011, (short)0b000'011'111, (short)0b001'001'111, (short)0b011'000'111};

int lastGreyCodeValue1 = 0;
int rotationValue1 = 0;

int lastGreyCodeValue2 = 0;
int rotationValue2 = 0;

void setup()
{
  pinMode(inputButton1, INPUT);
  pinMode(inputDT1, INPUT);
  pinMode(inputSW1, INPUT);

  pinMode(inputButton2, INPUT);
  pinMode(inputDT2, INPUT);
  pinMode(inputSW2, INPUT);

  pinMode(outputData, OUTPUT);
  pinMode(outputLatch, OUTPUT);
  pinMode(outputClock, OUTPUT);

  Serial.begin(115200);
}

void CalculateGreyCode(int DT, int SW, int *rotationValue, int *lastGreyCodeValue)
{
  int currentGreyCodeValue = DT + (SW << 1);
  int lastRotation;
  if (currentGreyCodeValue < 2)
  {
    currentGreyCodeValue += 1;
    currentGreyCodeValue %= 2;
  }

  int difference = currentGreyCodeValue - *lastGreyCodeValue;
  switch (difference)
  {
  case 1:
  case -3:
    lastRotation = -1;
    break;
  case 3:
  case -1:
    lastRotation = 1;
    break;
  default:
    lastRotation = 0;
    break;
  }

  *lastGreyCodeValue = currentGreyCodeValue;
  *rotationValue += lastRotation;
}

void readSerialDoubleDelimiter(char intDivision, char end, int maxCharLength = 4)
{
  std::string completeInt("");
  char currentChar;

  for (int i = 0; i < 8; i++)
  {
    completeInt = "";
    for (int j = 0; j < maxCharLength; j++)
    {
      currentChar = Serial.read();

      if (currentChar == intDivision)
      {
        outputDataValues[i] = atoi(completeInt.c_str());
        break;
      }
      if (currentChar == end)
      {
        outputDataValues[i] = atoi(completeInt.c_str());
        return;
      }

      completeInt += currentChar;
    }
  }
}

void loop()
{
  for (int i = 0; i < PWMDepth; i++)
  {
    for (int j = 0; j < 24; j++)
    {
      int shiftSize = (j % 3) * 3;

      int activeBitAmount = (outputDataValues[j / 3] >> shiftSize) & PWMDepthMask;
      int calculatedPWM = (((int)pow(2, PWMDepth) - 1) >> (PWMDepth - activeBitAmount));
      int currentDisplayedBit = (calculatedPWM >> i) & 1;

      digitalWrite(outputData, currentDisplayedBit);
      digitalWrite(outputClock, 0);
      digitalWrite(outputClock, 1);
    }
    digitalWrite(outputLatch, 0);
    digitalWrite(outputLatch, 1);
  }

  CalculateGreyCode(!digitalRead(inputDT1), !digitalRead(inputSW1), &rotationValue1, &lastGreyCodeValue1);
  CalculateGreyCode(!digitalRead(inputDT2), !digitalRead(inputSW2), &rotationValue2, &lastGreyCodeValue2);
  if (Serial.available() > 0)
  {
    readSerialDoubleDelimiter('.', '\n');

    // for (int i = 0; i < 8; i++)
    // {
    //   Serial.print(outputDataValues[i]);
    //   if (i < 7)
    //   {
    //     Serial.print("|");
    //   }
    // }
    // Serial.print(",");

    // TODO make a message parser and assign the serial data from python to the LED variable

    Serial.print(!digitalRead(inputButton1), BIN);
    Serial.print('|');
    Serial.print(rotationValue1);
    Serial.print(",");
    Serial.print(!digitalRead(inputButton2), BIN);
    Serial.print('|');
    Serial.print(rotationValue2);
    Serial.print('\n');
  }
}