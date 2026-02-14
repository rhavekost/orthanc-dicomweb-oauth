// ========================================
// Orthanc Configuration Module
// ========================================

@description('DICOM service URL')
param dicomServiceUrl string

@description('OAuth token endpoint')
param tokenEndpoint string

@description('OAuth scope')
param scope string

@description('OAuth client ID')
param clientId string

@description('OAuth client secret')
@secure()
param clientSecret string

@description('Orthanc DICOM AET')
param dicomAet string = 'ORTHANC'

@description('Orthanc HTTP port')
param httpPort int = 8042

@description('Orthanc DICOM port')
param dicomPort int = 4242

// ========================================
// Outputs
// ========================================

output orthancConfig object = {
  Name: dicomAet
  RemoteAccessAllowed: true
  AuthenticationEnabled: true
  HttpPort: httpPort
  HttpCompressionEnabled: true
  HttpThreadsCount: 50
  DicomAet: dicomAet
  DicomPort: dicomPort
  DicomThreadsCount: 4
  Plugins: [
    '/etc/orthanc/plugins/dicomweb_oauth_plugin.py'
  ]
}

output oauthPluginConfig object = {
  DicomWebOAuth: {
    ConfigVersion: '2.0'
    LogLevel: 'INFO'
    RateLimitRequests: 100
    RateLimitWindowSeconds: 60
    Servers: {
      'azure-dicom': {
        Url: dicomServiceUrl
        TokenEndpoint: tokenEndpoint
        Scope: scope
        TokenRefreshBufferSeconds: 300
        ClientId: clientId
        ClientSecret: clientSecret
        VerifySSL: true
      }
    }
  }
}
