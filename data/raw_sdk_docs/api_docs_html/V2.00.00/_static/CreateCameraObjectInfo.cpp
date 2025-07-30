// sample "CreateCameraObjectInfo"
#include <chrono>
#include <codecvt>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <future>
#include <iostream>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#if !defined(__APPLE__)
  #if defined(USE_EXPERIMENTAL_FS) // for jetson
    #include <experimental/filesystem>
    namespace fs = std::experimental::filesystem;
  #else
    #include <filesystem>
    namespace fs = std::filesystem;
  #endif
#endif

#if defined(__APPLE__) || defined(__linux__)
  #include <unistd.h>
#endif

// macro for multibyte character
#if defined(_WIN32) || defined(_WIN64)
  using CrString = std::wstring;
  #define CRSTR(s) L ## s
  #define CrCout std::wcout
  #define Utf8ToCr(a) wstring_convert.from_bytes(a)
  static std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>, wchar_t> wstring_convert;
#else
  using CrString = std::string;
  #define CRSTR(s) s
  #define CrCout std::cout
  #define Utf8ToCr(a) (a)
#endif


#include "CRSDK/CrDeviceProperty.h"
#include "CRSDK/CameraRemote_SDK.h"
#include "CRSDK/IDeviceCallback.h"
#include "CrDebugString.h"   // use CrDebugString.cpp

#define PrintError(msg, err) { fprintf(stderr, "Error in %s(%d):" msg ",%s\n", __FUNCTION__, __LINE__, (err ? CrErrorString(err).c_str():"")); }
#define GotoError(msg, err) { PrintError(msg, err); goto Error; }

bool  m_connected = false;
std::string m_modelId;

std::mutex m_eventPromiseMutex;
std::promise<void>* m_eventPromise = nullptr;
void setEventPromise(std::promise<void>* dp)
{
    std::lock_guard<std::mutex> lock(m_eventPromiseMutex);
    m_eventPromise = dp;
}

class DeviceCallback : public SCRSDK::IDeviceCallback
{
public:
    DeviceCallback() {};
    ~DeviceCallback() {};

    void OnConnected(SCRSDK::DeviceConnectionVersioin version)
    {
        std::cout << "Connected to " << m_modelId << "\n";
        m_connected = true;
        std::lock_guard<std::mutex> lock(m_eventPromiseMutex);
        if(m_eventPromise) {
            m_eventPromise->set_value();
            m_eventPromise = nullptr;
        }
    }

    void OnError(CrInt32u error)
    {
        printf("Connection error:%s\n", CrErrorString(error).c_str());
        std::lock_guard<std::mutex> lock(m_eventPromiseMutex);
        if(m_eventPromise) {
            m_eventPromise->set_exception(std::make_exception_ptr(std::runtime_error("error")));
            m_eventPromise = nullptr;
        }
    }

    void OnDisconnected(CrInt32u error)
    {
        std::cout << "Disconnected from " << m_modelId << "\n";
        m_connected = false;
        std::lock_guard<std::mutex> lock(m_eventPromiseMutex);
        if(m_eventPromise) {
            m_eventPromise->set_value();
            m_eventPromise = nullptr;
        }
    }

    void OnCompleteDownload(CrChar* filename, CrInt32u type )
    {
        CrCout << "OnCompleteDownload:" << filename << "\n";
    }

    void OnNotifyContentsTransfer(CrInt32u notify, SCRSDK::CrContentHandle contentHandle, CrChar* filename)
    {
        std::cout << "OnNotifyContentsTransfer.\n";
    }

    void OnWarning(CrInt32u warning)
    {
        if (warning == SCRSDK::CrWarning_Connect_Reconnecting) {
            std::cout << "Reconnecting to " << m_modelId << "\n";
            return;
        }
    }

    void OnWarningExt(CrInt32u warning, CrInt32 param1, CrInt32 param2, CrInt32 param3) {}
    void OnLvPropertyChanged() {}
    void OnLvPropertyChangedCodes(CrInt32u num, CrInt32u* codes) {}
    void OnPropertyChanged() {}
    void OnPropertyChangedCodes(CrInt32u num, CrInt32u* codes) {}
};

std::vector<std::string> _split(std::string inputLine, char delimiter)
{
    std::vector<std::string> strArray;
    if (inputLine.empty()) return strArray;

    std::string tmp;
    std::stringstream ss{inputLine};
    while (getline(ss, tmp, delimiter)) {
        strArray.push_back(tmp);
    }
    return strArray;
}

const std::unordered_map<std::string, uint32_t> map_CrCameraDeviceModel
{
    { "ILCE-7RM4", SCRSDK::CrCameraDeviceModel_ILCE_7RM4 },
    { "ILCE-9M2", SCRSDK::CrCameraDeviceModel_ILCE_9M2 },
    { "ILCE-7C", SCRSDK::CrCameraDeviceModel_ILCE_7C },
    { "ILCE-7SM3", SCRSDK::CrCameraDeviceModel_ILCE_7SM3 },
    { "ILCE-1", SCRSDK::CrCameraDeviceModel_ILCE_1 },
    { "ILCE-7RM4A", SCRSDK::CrCameraDeviceModel_ILCE_7RM4A },
    { "DSC-RX0M2", SCRSDK::CrCameraDeviceModel_DSC_RX0M2 },
    { "ILCE-7M4", SCRSDK::CrCameraDeviceModel_ILCE_7M4 },
    { "ILME-FX3", SCRSDK::CrCameraDeviceModel_ILME_FX3 },
    { "ILME-FX30", SCRSDK::CrCameraDeviceModel_ILME_FX30 },
    { "ILME-FX6", SCRSDK::CrCameraDeviceModel_ILME_FX6 },
    { "ILCE-7RM5", SCRSDK::CrCameraDeviceModel_ILCE_7RM5 },
    { "ZV-E1", SCRSDK::CrCameraDeviceModel_ZV_E1 },
    { "ILCE-6700", SCRSDK::CrCameraDeviceModel_ILCE_6700 },
    { "ILCE-7CM2", SCRSDK::CrCameraDeviceModel_ILCE_7CM2 },
    { "ILCE-7CR", SCRSDK::CrCameraDeviceModel_ILCE_7CR },
    { "ILX-LR1", SCRSDK::CrCameraDeviceModel_ILX_LR1 },
    { "MPC-2610", SCRSDK::CrCameraDeviceModel_MPC_2610 },
    { "ILCE-9M3", SCRSDK::CrCameraDeviceModel_ILCE_9M3 },
    { "ZV-E10M2", SCRSDK::CrCameraDeviceModel_ZV_E10M2 },
    { "PXW-Z200", SCRSDK::CrCameraDeviceModel_PXW_Z200 },
    { "HXR-NX800", SCRSDK::CrCameraDeviceModel_HXR_NX800 },
    { "ILCE-1M2", SCRSDK::CrCameraDeviceModel_ILCE_1M2 },
//  { "xx", SCRSDK::CrCameraDeviceModel_xx },
    { "BRC-AM7", SCRSDK::CrCameraDeviceModel_BRC_AM7 },
    { "ILME-FR7", SCRSDK::CrCameraDeviceModel_ILME_FR7 },
//  { "yy", SCRSDK::CrCameraDeviceModel_yy },
};

int main(void)
{
    int result = -1;
    SCRSDK::CrError err = SCRSDK::CrError_None;
    int64_t  m_device_handle = 0;
    SCRSDK::ICrCameraObjectInfo* objInfo = nullptr;
    DeviceCallback deviceCallback;

  #if defined(__APPLE__)
    #define MAC_MAX_PATH 255
    char pathBuf[MAC_MAX_PATH] = {0};
    if(NULL == getcwd(pathBuf, sizeof(pathBuf) - 1)) return 1;
    CrString path = pathBuf;
  #else
    CrString path = fs::current_path().native();
  #endif

    bool boolRet = SCRSDK::Init();
    if(!boolRet) GotoError("", 0);

    {
        std::string inputLine;
        uint32_t model = 0;
        std::string  userId = "";
        std::string  userPassword = "";

        std::cout << "usage:usb <model> <usb serial>\n";
        std::cout << "      ip  <model> <ipaddress> [userid] [pass]\n";
        std::getline(std::cin, inputLine);
        std::vector<std::string> args = _split(inputLine, ' ');
        if(args.size() < 3) GotoError("invalid input", 0);

        {
            auto iter = map_CrCameraDeviceModel.find(args[1]);
            if(iter == end(map_CrCameraDeviceModel)) {
                std::cout << "unknown model\n";
                if(args[0] == "usb") GotoError("", 0);
                model = SCRSDK::CrCameraDeviceModel_ILCE_1;
            } else {
                model = iter->second;
            }
        }

        if(args[0] == "usb") {
            err = SCRSDK::CreateCameraObjectInfoUSBConnection(&objInfo, (SCRSDK::CrCameraDeviceModelList)model, (CrInt8u*)Utf8ToCr(args[2]).c_str());

        } else if(args[0] == "ip") {
            CrInt8u macAddress[6] = {0};
            CrInt32u ipAddress = 0;
            bool SSHsupport = false;

            std::vector<std::string> ips = _split(args[2], '.');
            if(ips.size() < 4) GotoError("invalid input", 0);
            for(int i = 0; i < 4; i++) {
                try { ipAddress |= stoi(ips[i]) << (i*8); } catch(const std::exception&) { GotoError("invalid input", 0); }
            }

            if(args.size() >= 5) {
                SSHsupport = true;
                userId = args[3];
                userPassword = args[4];
            }
            err = SCRSDK::CreateCameraObjectInfoEthernetConnection(&objInfo, (SCRSDK::CrCameraDeviceModelList)model, ipAddress, macAddress, SSHsupport);
        } else {
            GotoError("invalid input", 0);
        }
        if(err || objInfo == nullptr) GotoError("", err);

        m_modelId = args[1].append("(").append(args[2]).append(")");

        // connect
        {
            char fpBuff[128] = {0};
            CrInt32u fpLen = 0;
            std::promise<void> eventPromise;
            std::future<void> eventFuture = eventPromise.get_future();

            if (objInfo->GetSSHsupport() == SCRSDK::CrSSHsupport_ON) {
                SCRSDK::CrError err = SCRSDK::GetFingerprint(objInfo, fpBuff, &fpLen);
                if(err) GotoError("", err);
                std::cout << "fingerprint: " << fpBuff << "\n";
            }

            setEventPromise(&eventPromise);
            err = SCRSDK::Connect(objInfo, &deviceCallback, &m_device_handle,
                SCRSDK::CrSdkControlMode_Remote,
                SCRSDK::CrReconnecting_ON,
                userId.c_str(), userPassword.c_str(), fpBuff, fpLen);
            if(err) GotoError("", err);

        //  std::future_status status = eventFuture.wait_for(std::chrono::milliseconds(3000));
        //  if(status != std::future_status::ready) GotoError("timeout",0);
            try{
                eventFuture.get();
            } catch(const std::exception&) GotoError("", 0);
        }
    }

    // set work directory
    {
        CrCout << "path=" << path.data() << "\n";
        err = SCRSDK::SetSaveInfo(m_device_handle, const_cast<CrChar*>(path.data()), const_cast<CrChar*>(CRSTR("DSC")), -1/*startNo*/);
        if(err) GotoError("", err);
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    std::cout << "usage:\n";
    std::cout << "To exit, please enter 'q'.\n";

    while(1) {
        std::string inputLine;
        std::getline(std::cin, inputLine);
        if(inputLine == "q" || inputLine == "Q") {
            break;
        }
        std::cout << "unknown DP nor CMD\n";
    }

    result = 0;
Error:
    if(objInfo) objInfo->Release();

    if(m_connected) {
        std::promise<void> eventPromise;
        std::future<void> eventFuture = eventPromise.get_future();
        setEventPromise(&eventPromise);
        SCRSDK::Disconnect(m_device_handle);
        eventFuture.wait_for(std::chrono::milliseconds(3000));
    }
    if(m_device_handle) SCRSDK::ReleaseDevice(m_device_handle);
    SCRSDK::Release();

    return result;
}
