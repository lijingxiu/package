Pod::Spec.new do |s|  
    s.name              = 'TestPodCC'
    s.version           = '9.10.0'
    s.summary           = '测试'
    s.homepage          = 'http://zhipin.com/'

    s.author            = { 'liqiang' => 'liqiang05@kanzhun.com' }
    s.license           = "MIT"

    s.platform          = :ios
    s.source            = { :git => 'https://github.com/haivy/TestCC.git', :tag => s.version }
    s.resource          = [ 'Products/**/*.{xcasset,bundle}' ]
    s.source_files  = "Products/TestCC.framework/**/*.h"
    s.public_header_files = "Products/TestCC.framework/**/*.h"

    s.ios.deployment_target = '9.0'
    s.ios.vendored_frameworks = 'Products/TestCC.framework'
end
