package com.example.aoatest;

import java.lang.*;
import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.zip.CRC32;
import java.util.zip.Checksum;

import android.os.ParcelFileDescriptor;
import android.util.Log;

public class AoaTest implements Runnable {
    private static final String TAG = "AoaTest";

    FileInputStream mInputStream;
    FileOutputStream mOutputStream;
    Thread mThread;

    public void start(ParcelFileDescriptor fileDescriptor) {
        FileDescriptor fd = fileDescriptor.getFileDescriptor();
        mInputStream = new FileInputStream(fd);
        mOutputStream = new FileOutputStream(fd);
        mThread = new Thread(null, this, "AosTest");
        mThread.start();
    }

    public void stop() {
        if (mInputStream != null) {
            try {
                mInputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
            mInputStream = null;
        }
        if (mOutputStream != null) {
            try {
                mOutputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
            mOutputStream = null;
        }

        if (mThread != null) {
            Log.d(TAG, "interrpt thread to stop");
            mThread.interrupt();
            Log.d(TAG, "wait...");
            try {
                mThread.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            Log.d(TAG, "wait...done");
            mThread = null;
        }
    }

    private void log_e(String str) {
        Log.e(TAG, str);
    }
    private void log_i(String str) {
        Log.i(TAG, str);
    }
    private void log_d(String str) {
        Log.d(TAG, str);
    }

    public void run() {
        int testInputCount = 0;
        int testInputCRC = 0;
        boolean testInputNoCRC = true;
        Checksum testInputChecksum = null;
        long testInputStart = 0;
        long testInputEnd = 0;
        int inputTotal = 0;

        int testOutputCount = 0;
        int testOutputCRC = 0;
        boolean testOutputNoCRC = true;
        Checksum testOutputChecksum = null;
        long testOutputStart = 0;
        long testOutputEnd = 0;
        int outputTotal = 0;

        final int HEADER_SIZE = 8;
        final int BUFFER_SIZE = 1024*1024;
        byte[] buf = new byte[BUFFER_SIZE];
        int n;

        try {
            Thread.sleep(1000);
            String str = "Hello";
            send(str.getBytes());

            while (true) {
                if (0 < testInputCount || 0 < testOutputCount) {
                    /*
                     * send or receive test data stream
                     */
                    if (0 < testInputCount) {
                        /*
                         * receive test data stream
                         */
                        n = Math.min(Math.min(testInputCount, BUFFER_SIZE),
                                     mInputStream.available());
                        n = mInputStream.read(buf, 0, n);
                        if (!testInputNoCRC)
                            testInputChecksum.update(buf, 0, n);
                        testInputCount -= n;
                        inputTotal += n;
                        log_d(String.format("%d bytes recieved, %d bytes remain, CRC=%08x",
                                            n, testInputCount, testInputCRC));
                        if (testInputCount == 0) {
                            long crc = 0;
                            log_d(String.format("%d bytes in the buffer",
                                                mInputStream.available()));
                            testInputEnd = System.currentTimeMillis();
                            n = mInputStream.read(buf, 0, 4);
                            assert n == 4;
                            crc = Utils.getUint32(buf, 4);
                            if (!testInputNoCRC)
                                testInputCRC = (int)testInputChecksum.getValue();
                            testInputChecksum = null;
                            log_i(String.format("%d bytes recieved in %7.3f sec, CRC: %08x%s%08x",
                                  inputTotal,
                                  (testInputEnd - testInputStart) / 1000.0,
                                  (int)crc,
                                  (crc == testInputCRC) ? "==" : "!=",
                                  testInputCRC));
                        }
                    }

                    if (0 < testOutputCount) {
                        /*
                         * send test data stream
                         */
                        n = Math.min(testOutputCount, BUFFER_SIZE);
                        mOutputStream.write(buf, 0, n);
                        if (!testOutputNoCRC)
                            testOutputChecksum.update(buf, 0, n);
                        testOutputCount -= n;
                        outputTotal += n;
                        log_d(String.format("%d bytes sent, %d bytes remain, CRC=%08x",
                                            n, testInputCount, testInputCRC));
                        if (testOutputCount == 0) {
                            testOutputEnd  = System.currentTimeMillis();
                            if (!testOutputNoCRC)
                                testOutputCRC = (int)testOutputChecksum.getValue();
                            testOutputChecksum = null;
                            Utils.putUint32(buf, 0, testOutputCRC);
                            mOutputStream.write(buf, 0, 4);
                            log_i(String.format("%d bytes sent in %7.3f sec, CRC: %08x",
                                  outputTotal,
                                  (testOutputEnd - testOutputStart) / 1000.0,
                                  testOutputCRC));
                        }
                    }
                } else {
                    /*
                     * receive command
                     */
                    String command = null;
                    //n = mInputStream.read(buf, 0, HEADER_SIZE);
                    n = mInputStream.read(buf, 0, BUFFER_SIZE);
                    if (HEADER_SIZE <= n) {
                        Utils.dumpHex(buf, 0, n, (line) -> {
                                log_i(String.format("HEADER: %s", line)); });
                        command = new String(Arrays.copyOfRange(buf, 0, 4),
                                             StandardCharsets.UTF_8);
                    }

                    if (command != null && (command.equals("\\TRC") || command.equals("\\TR_"))) {
                        /*
                         * comand: test receive with or w/o crc
                         */
                        if (buf[3] == 'C') {
                            testInputNoCRC = false;
                            testInputChecksum = new CRC32();
                        } else {
                            testInputNoCRC = true;
                        }
                        testInputCRC = 0x01234567;
                        testInputCount = Utils.getUint32(buf, 4);
                        testInputStart = System.currentTimeMillis();
                        testInputEnd = 0;
                        log_i(String.format("testInputCount=%u CRC=%08x",
                                            testInputCount, testInputCRC));
                    } else
                    if (command != null && (command.equals("\\TSC") || command.equals("\\TS_"))) {
                        /*
                         * command: test send with or w/o crc
                         */
                        if (buf[3] == 'C') {
                            testOutputNoCRC = false;
                            testOutputChecksum = new CRC32();
                        } else {
                            testOutputNoCRC = true;
                        }
                        testOutputCRC = 0x01234567;
                        // FIXME: should be filled with random data
                        Arrays.fill(buf, (byte)0);
                        testOutputCount = Utils.getUint32(buf, 4);
                        testOutputStart = System.currentTimeMillis();
                        testOutputEnd = 0;
                        log_i(String.format("testOutputCount=%d CRC=%08x",
                                            testOutputCount, testOutputCRC));
                    } else
                    if (command != null && command.equals("\\TGS")) {
                        /*
                         * command: test get status
                         */
                        log_i(String.format("Test Get Status: %d %08x %d %08x",
                                            inputTotal, testInputCRC,
                                            outputTotal, testOutputCRC));
                        Utils.putUint32(buf, 0, inputTotal);
                        Utils.putUint32(buf, 4, testInputCRC);
                        Utils.putUint32(buf, 8, outputTotal);
                        Utils.putUint32(buf, 12, testOutputCRC);
                        mOutputStream.write(buf, 0, 16);
                    } else
                    if (command != null && command.equals("\\TRS")) {
                        /*
                         * command: test reset status
                         */
                        log_i("Test Reset Status");
                        testInputCount = 0;
                        testInputCRC = 0;
                        inputTotal = 0;
                        testOutputCount = 0;
                        testOutputCRC = 0;
                        outputTotal = 0;
                    } else
                    if (command != null && command.equals("\\MSG")) {
                        /*
                         * command: message from accessory
                         */
                        n = Utils.getUint32(buf, 4);
                        log_i(String.format("Message %d bytes from accessory", n));
                        Utils.dumpHex(buf, 8, n, (line) -> { log_i(line); });
                    } else
                    {
                        log_i("Unknown command from accessory");
                        Utils.dumpHex(buf, 0, n, (line) -> { log_i(line); });
                    }
                }
            }
        } catch (Exception ex) {
            Log.e(TAG, "", ex);
        }
        log_i("thread terminated.");
    }

    public void send(byte[] buffer) {
        for (int i = 0; i < 10; i++) {
            if (mOutputStream != null) {
                try {
                    Log.d(TAG, "send data to the stream.");
                    mOutputStream.write(buffer);
                    break;
                } catch (IOException e) {
                    Log.e(TAG, "write failed", e);
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException e1) {
                        e1.printStackTrace();
                    }
                }
            }
        }
    }
}
