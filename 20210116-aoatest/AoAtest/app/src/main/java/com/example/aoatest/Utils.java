package com.example.aoatest;

import java.util.Arrays;

interface LogOutputFunction {
    void output(String str);
}

public class Utils {
    private static final char[] HEX_ARRAY = "0123456789ABCDEF".toCharArray();

    public static String bytesToHex(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = HEX_ARRAY[v >>> 4];
            hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
        }

        return new String(hexChars);
    }

    public static void dumpHex(byte[] bytes, int len, LogOutputFunction log) {
        char[] line = new char[65];
        int i;

        for (i = 0; i < len; i++) {
            int offset = i % 16;
            int value = bytes[i] & 0xFF;
            if (offset == 0) {
                Arrays.fill(line, ' ');
            }
            line[offset * 2    ] = HEX_ARRAY[value >>> 4];
            line[offset * 2 + 1] = HEX_ARRAY[value & 0x0f];
            if (Character.isISOControl(bytes[i]))
                line[49 + offset] = '.';
            else
                line[49 + offset] = (char)(bytes[i] & 0xff);
            if (offset == 15)
                log.output(String.format("%04x: ", i & ~0xf) + String.valueOf(line));
        }
        if (i % 16 != 0)
            log.output(String.format("%04x: ", i & ~0xf) + String.valueOf(line));
    }
}
