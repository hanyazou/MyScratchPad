package com.example.aoatest;

import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

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

    public void run() {
        int ret = 0;
        byte[] buffer = new byte[4096];

        try {
            Thread.sleep(1000);
            String str = "Hello";
            send(str.getBytes());
        } catch (Exception e) {
        }
        while (mInputStream != null) {
            try {
                ret = mInputStream.read(buffer);
            } catch (IOException e) {
                Log.e(TAG, "read failed", e);
                break;
            }
            Log.d(TAG, ret + " bytes read from USB accessory.");
            Utils.dumpHex(buffer, ret, (line) -> { Log.d(TAG, line); });
        }
        Log.d(TAG, "thread terminated.");
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
