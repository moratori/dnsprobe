# InfluxDB schema description

測定後のキーの存在状況

|KeyType |name            |SOA measurement   | DNSKEY measurement | NS measurement   |
| ----   | ----           | ----             | ----               | ----             |
|tagKey  |af              |    〇            |     〇             |    〇            |
|tagKey  |dst_addr        |    〇            |     〇             |    〇            |
|tagKey  |dst_name        |    〇            |     〇             |    〇            |
|tagKey  |error_class_name|    〇            |     〇             |    〇            |
|tagKey  |got_response    |    〇            |     〇             |    〇            |
|tagKey  |nsid            |    〇            |     〇             |    〇            |
|tagKey  |prb_id          |    〇            |     〇             |    〇            |
|tagKey  |prb_lat         |    〇            |     〇             |    〇            |
|tagKey  |prb_lon         |    〇            |     〇             |    〇            |
|tagKey  |proto           |    〇            |     〇             |    〇            |
|tagKey  |qname           |    〇            |     〇             |    〇            |
|tagKey  |rrtype          |    〇            |     〇             |    〇            |
|tagKey  |src_addr        |    〇            |     〇             |    〇            |
|fieldkey|data            |                |(正常:?,異常:)   |(正常:〇,異常:) |
|fieldkey|id              |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|mname           |(正常:〇,異常:) |(正常:,異常:)   |(正常:,異常:) |
|fieldkey|name            |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|probe_asn       |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|probe_asn_desc  |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|probe_uptime    |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|reason          |(正常:,異常:〇) |(正常:,異常:〇)   |(正常:,異常:〇) |
|fieldkey|rname           |(正常:〇,異常:) |(正常:,異常:)   |(正常:,異常:) |
|fieldkey|serial          |(正常:〇,異常:) |(正常:,異常:)   |(正常:,異常:) |
|fieldkey|time_took       |(正常:〇,異常:〇) |(正常:〇,異常:〇)   |(正常:〇,異常:〇) |
|fieldkey|ttl             |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |
|fieldkey|type            |(正常:〇,異常:) |(正常:〇,異常:)   |(正常:〇,異常:) |

?: コンフィグに依存する
