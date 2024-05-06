# Script to auto renew/confirm noip.com free hosts

[noip.com](https://www.noip.com/) free hosts expire every month.
This script auto clicks web pages to renew the hosts,
using Python/Selenium with Chrome headless mode.

- Original author: [loblab](https://github.com/loblab), [IDemixI](https://www.github.com/IDemixI)
- Platform: Linux / Windows (No GUI needed); Python 3.10+

![noip.com hosts](https://raw.githubusercontent.com/loblab/noip-renew/master/screenshot.png)

## Usage

1. Clone this repository to the device you will be running it from. (`git clone https://github.com/YFHD-osu/noip-renew.git`)
2. Run ``mail.py`` to set up Gmail API for recieving 2FA verification code 
3. Run ``noip-renew.py`` with parameter to renew hosts 

**More information can be found in [wiki](https://github.com/YFHD-osu/noip-renew/wiki) page**

## Remarks

The script is not designed to renew/update the dynamic DNS records, though the latest version does have this ability if requested.
Check [noip.com documentation](https://www.noip.com/integrate) for that purpose.
Most wireless routers support noip.com. For more information, check [here](https://www.noip.com/support/knowledgebase/what-devices-support-no-ips-dynamic-dns-update-service/).
You can also check [DNS-O-Matic](https://dnsomatic.com/) to update multiple noip.com DNS records.

If you need notification functionality, please try [IDemixI's branch](https://github.com/IDemixI/noip-renew/tree/notifications).
