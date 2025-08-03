package com.example.myapplication;

import android.Manifest;
import android.content.ContentValues;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.telephony.*;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private static final int PERMISSION_REQUEST_CODE = 1;
    private static final String API_TOKEN = "pk.99d58c03d2e3e7edfd2abb2628353e06"; // Kept hardcoded as requested

    // A simple data class to hold all cell information
    private static class CellData {
        String type = "", cid = "", tac = "", nci = "", rsrp = "", rsrq = "", dbm = "", level = "", mcc = "", mnc = "";
        String lat = "N/A", lon = "N/A", address = "N/A";

        // Method to generate a CSV row string
        public String toCsvRow() {
            // Handles commas in the address by enclosing it in quotes
            return String.join(",",
                    type, cid, tac, nci, rsrp, rsrq, dbm, level, mcc, mnc, lat, lon, "\"" + address.replace("\"", "\"\"") + "\""
            ) + "\n";
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestPermissions();
    }

    private void requestPermissions() {
        ArrayList<String> permissionsToRequest = new ArrayList<>();
        permissionsToRequest.add(Manifest.permission.ACCESS_FINE_LOCATION);
        permissionsToRequest.add(Manifest.permission.READ_PHONE_STATE);
        permissionsToRequest.add(Manifest.permission.INTERNET);

        // Request storage permission only on older Android versions (below Q)
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            permissionsToRequest.add(Manifest.permission.WRITE_EXTERNAL_STORAGE);
        }

        ActivityCompat.requestPermissions(this, permissionsToRequest.toArray(new String[0]), PERMISSION_REQUEST_CODE);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == PERMISSION_REQUEST_CODE) {
            boolean allPermissionsGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allPermissionsGranted = false;
                    break;
                }
            }

            if (allPermissionsGranted) {
                startCellInfoCollection();
            } else {
                Toast.makeText(this, "Permissions denied. Cannot function.", Toast.LENGTH_LONG).show();
            }
        }
    }

    private void startCellInfoCollection() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            // Safety check
            return;
        }

        TelephonyManager telephonyManager = (TelephonyManager) getSystemService(TELEPHONY_SERVICE);
        telephonyManager.requestCellInfoUpdate(getMainExecutor(), new TelephonyManager.CellInfoCallback() {
            @Override
            public void onCellInfo(List<CellInfo> cellInfoList) {
                if (cellInfoList == null || cellInfoList.isEmpty()) {
                    Toast.makeText(MainActivity.this, "No cell info available", Toast.LENGTH_SHORT).show();
                    return;
                }

                List<CellData> collectedData = new ArrayList<>();
                for (CellInfo info : cellInfoList) {
                    if (!info.isRegistered()) continue;

                    CellData data = new CellData();
                    if (info instanceof CellInfoLte) {
                        data.type = "LTE";
                        CellIdentityLte id = ((CellInfoLte) info).getCellIdentity();
                        CellSignalStrengthLte ss = ((CellInfoLte) info).getCellSignalStrength();
                        data.cid = String.valueOf(id.getCi());
                        data.tac = String.valueOf(id.getTac());
                        data.nci = data.cid;
                        data.rsrp = String.valueOf(ss.getRsrp());
                        data.rsrq = String.valueOf(ss.getRsrq());
                        data.dbm = String.valueOf(ss.getDbm());
                        data.level = String.valueOf(ss.getLevel());
                        data.mcc = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R ? id.getMccString() : String.valueOf(id.getMcc());
                        data.mnc = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R ? id.getMncString() : String.valueOf(id.getMnc());
                    } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && info instanceof CellInfoNr) {
                        data.type = "5G";
                        CellIdentityNr id = (CellIdentityNr) ((CellInfoNr) info).getCellIdentity();
                        CellSignalStrengthNr ss = (CellSignalStrengthNr) ((CellInfoNr) info).getCellSignalStrength();
                        data.nci = String.valueOf(id.getNci());
                        data.tac = String.valueOf(id.getTac());
                        data.dbm = String.valueOf(ss.getDbm());
                        data.level = String.valueOf(ss.getLevel());
                        data.mcc = id.getMccString();
                        data.mnc = id.getMncString();
                        data.cid = data.nci;
                    } else if (info instanceof CellInfoWcdma) {
                        data.type = "WCDMA";
                        CellIdentityWcdma id = ((CellInfoWcdma) info).getCellIdentity();
                        CellSignalStrengthWcdma ss = ((CellInfoWcdma) info).getCellSignalStrength();
                        data.cid = String.valueOf(id.getCid());
                        data.tac = String.valueOf(id.getLac());
                        data.nci = data.cid;
                        data.dbm = String.valueOf(ss.getDbm());
                        data.level = String.valueOf(ss.getLevel());
                        data.mcc = String.valueOf(id.getMcc());
                        data.mnc = String.valueOf(id.getMnc());
                    } else if (info instanceof CellInfoGsm) {
                        data.type = "GSM";
                        CellIdentityGsm id = ((CellInfoGsm) info).getCellIdentity();
                        CellSignalStrengthGsm ss = ((CellInfoGsm) info).getCellSignalStrength();
                        data.cid = String.valueOf(id.getCid());
                        data.tac = String.valueOf(id.getLac());
                        data.nci = data.cid;
                        data.dbm = String.valueOf(ss.getDbm());
                        data.level = String.valueOf(ss.getLevel());
                        data.mcc = String.valueOf(id.getMcc());
                        data.mnc = String.valueOf(id.getMnc());
                    }

                    if (data.mcc != null && !data.mcc.isEmpty() && !data.mcc.equals("0") && data.cid != null && !data.cid.equals("0") && !data.cid.equals("-1")) {
                        collectedData.add(data);
                    }
                }

                if (!collectedData.isEmpty()) {
                    fetchAllTowerLocations(collectedData);
                } else {
                    Toast.makeText(MainActivity.this, "No registered cell towers found.", Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void fetchAllTowerLocations(List<CellData> dataList) {
        // Use a fixed thread pool for efficiency instead of creating new threads manually
        ExecutorService executor = Executors.newFixedThreadPool(Math.min(dataList.size(), 5));
        OkHttpClient client = new OkHttpClient();
        // Use CountDownLatch to wait for all threads to complete before saving the file
        CountDownLatch latch = new CountDownLatch(dataList.size());

        Toast.makeText(this, "Fetching tower locations...", Toast.LENGTH_SHORT).show();

        for (CellData data : dataList) {
            executor.submit(() -> {
                try {
                    // Use the correct radio type for the API call
                    String radioType = data.type.toLowerCase();
                    if (radioType.equals("5g")) radioType = "nr"; // Unwired API uses "nr" for 5G

                    String json = "{" +
                            "\"token\": \"" + API_TOKEN + "\"," +
                            "\"radio\": \"" + radioType + "\"," +
                            "\"mcc\": " + data.mcc + "," +
                            "\"mnc\": " + data.mnc + "," +
                            "\"cells\": [{\"lac\": " + data.tac + ", \"cid\": " + data.cid + "}]," +
                            "\"address\": 1" +
                            "}";

                    RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
                    Request request = new Request.Builder()
                            .url("https://us1.unwiredlabs.com/v2/process.php")
                            .post(body)
                            .build();

                    Response response = client.newCall(request).execute();
                    if (response.isSuccessful() && response.body() != null) {
                        String responseBody = response.body().string();
                        JSONObject obj = new JSONObject(responseBody);
                        // Update the CellData object with location info
                        if ("ok".equals(obj.optString("status"))) {
                            data.lat = obj.optString("lat", "N/A");
                            data.lon = obj.optString("lon", "N/A");
                            data.address = obj.optString("address", "N/A");
                        }
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                } finally {
                    latch.countDown(); // Signal that this task is complete
                }
            });
        }
        executor.shutdown();

        // This new thread waits until all network tasks are done, then builds and saves the CSV
        new Thread(() -> {
            try {
                latch.await(); // Blocks until latch count is zero
                buildAndSaveCsv(dataList);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }).start();
    }

    private void buildAndSaveCsv(List<CellData> dataList) {
        StringBuilder csvBuilder = new StringBuilder();
        csvBuilder.append("Type,CellID,TAC/PSC,NCI/ECI/CI,RSRP,RSRQ,dBm,Level,MCC,MNC,Lat,Lon,Address\n");

        for (CellData data : dataList) {
            csvBuilder.append(data.toCsvRow());
        }

        // Switch to the main thread to save the file and show a Toast
        runOnUiThread(() -> saveCsvToDownloads(csvBuilder.toString()));
    }

    private void saveCsvToDownloads(String csvData) {
        String fileName = "tower_signals.csv";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
            values.put(MediaStore.Downloads.MIME_TYPE, "text/csv");
            values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);

            Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri != null) {
                try (OutputStream outputStream = getContentResolver().openOutputStream(uri)) {
                    outputStream.write(csvData.getBytes());
                    Toast.makeText(this, "SUCCESS: CSV saved to Downloads", Toast.LENGTH_LONG).show();
                } catch (IOException e) {
                    e.printStackTrace();
                    Toast.makeText(this, "Failed to write file", Toast.LENGTH_SHORT).show();
                }
            }
        } else {
            File file = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), fileName);
            try (FileWriter writer = new FileWriter(file, false)) {
                writer.write(csvData);
                Toast.makeText(this, "SUCCESS: CSV saved to Downloads", Toast.LENGTH_LONG).show();
            } catch (IOException e) {
                e.printStackTrace();
                Toast.makeText(this, "Error saving file", Toast.LENGTH_SHORT).show();
            }
        }
    }
}