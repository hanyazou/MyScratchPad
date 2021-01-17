package com.example.aoatest;

import java.util.Arrays;

interface LogOutputFunction {
    void output(String str);
}

public class Utils {
    private static final char[] HEX_ARRAY = "0123456789ABCDEF".toCharArray();

    public static long getUint32(byte[] buf, int ofs) {
        return (buf[ofs + 0] & 0xff) << 24 | (buf[ofs + 1] & 0xff) << 16 |
            (buf[ofs + 2]  & 0xff) << 8 | (buf[ofs + 3] & 0xff);
    }

    public static void putUint32(byte[] buf, int ofs, long val) {
        buf[ofs + 0] = (byte)((val >> 24) & 0xff);
        buf[ofs + 1] = (byte)((val >> 16) & 0xff);
        buf[ofs + 2] = (byte)((val >>  8) & 0xff);
        buf[ofs + 3] = (byte)((val >>  0) & 0xff);
    }

    public static String bytesToHex(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = HEX_ARRAY[v >>> 4];
            hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
        }

        return new String(hexChars);
    }

    public static void dumpHex(byte[] bytes, int ofs, int len, LogOutputFunction log) {
        char[] line = new char[65];
        int i;

        for (i = 0; i < len; i++) {
            int offset = i % 16;
            int value = bytes[i + ofs] & 0xFF;
            if (offset == 0)
                Arrays.fill(line, ' ');
            line[offset * 3    ] = HEX_ARRAY[value >>> 4];
            line[offset * 3 + 1] = HEX_ARRAY[value & 0x0f];
            if (Character.isISOControl(bytes[i + ofs]))
                line[49 + offset] = '.';
            else
                line[49 + offset] = (char)(bytes[i + ofs] & 0xff);
            if (offset == 15)
                log.output(String.format("%04x: ", i & ~0xf) + String.valueOf(line));
        }
        if (i % 16 != 0)
            log.output(String.format("%04x: ", i & ~0xf) + String.valueOf(line));
    }
}
