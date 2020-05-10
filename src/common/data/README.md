# InfluxDB schema description

## database

```
CREATE DATABASE "dnsprobe"
```

## retention policies

```
CREATE RETENTION POLICY "rp_mes_dnsprobe"                                on "dnsprobe"    DURATION   730h REPLICATION 1 DEFAULT

CREATE RETENTION POLICY "rp_mes_cq_probe_versus_nameserver_availability" on "dnsprobe"    DURATION  2190h REPLICATION 1
CREATE RETENTION POLICY "rp_mes_cq_nameserver_availability"              on "dnsprobe"    DURATION  8760h REPLICATION 1
CREATE RETENTION POLICY "rp_mes_nameserver_availability"                 on "dnsprobe"    DURATION 17520h REPLICATION 1

CREATE RETENTION POLICY "rp_mes_cq_tcp_nameserver_availability"          on "dnsprobe"    DURATION  8760h REPLICATION 1
CREATE RETENTION POLICY "rp_mes_tcp_nameserver_availability"             on "dnsprobe"    DURATION 17520h REPLICATION 1

CREATE RETENTION POLICY "rp_mes_cq_udp_nameserver_availability"          on "dnsprobe"    DURATION  8760h REPLICATION 1
CREATE RETENTION POLICY "rp_mes_udp_nameserver_availability"             on "dnsprobe"    DURATION 17520h REPLICATION 1
```

## continuous queries

### for calculation of DNS name server availability
```
CREATE CONTINUOUS QUERY "mes_cq_probe_versus_nameserver_availability"
ON "dnsprobe"
BEGIN
    SELECT max(got_response_field) 
        INTO "dnsprobe"."rp_mes_cq_probe_versus_nameserver_availability"."mes_cq_probe_versus_nameserver_availability"
    FROM 
        "dnsprobe"."rp_mes_dnsprobe"."mes_dnsprobe"
    WHERE
        rrtype = 'SOA'
    GROUP BY time(1m), dst_name, af, prb_id fill(1)
END
```

```
CREATE CONTINUOUS QUERY "mes_cq_nameserver_availability"
ON "dnsprobe"
BEGIN
    SELECT mode(max) 
        INTO "dnsprobe"."rp_mes_cq_nameserver_availability"."mes_cq_nameserver_availability"
    FROM
        "dnsprobe"."rp_mes_cq_probe_versus_nameserver_availability"."mes_cq_probe_versus_nameserver_availability"
    GROUP BY time(1m), dst_name, af fill(1)
END
```

### for calculation of TCP DNS resolution RTT
```
CREATE CONTINUOUS QUERY "mes_cq_tcp_nameserver_availability"
ON "dnsprobe"
BEGIN
    SELECT mode(slr_exceeded_field)
        INTO "dnsprobe"."rp_mes_cq_tcp_nameserver_availability"."mes_cq_tcp_nameserver_availability"
    FROM 
        "dnsprobe"."rp_mes_dnsprobe"."mes_dnsprobe"
    WHERE 
        rrtype = 'SOA' AND 
        proto = 'tcp'
    GROUP BY time(1m), dst_name, af fill(0)
END
```

### for calculation of UDP DNS resolution RTT
```
CREATE CONTINUOUS QUERY "mes_cq_udp_nameserver_availability"
ON "dnsprobe"
BEGIN
    SELECT mode(slr_exceeded_field)
        INTO "dnsprobe"."rp_mes_cq_udp_nameserver_availability"."mes_cq_udp_nameserver_availability"
    FROM 
        "dnsprobe"."rp_mes_dnsprobe"."mes_dnsprobe"
    WHERE 
        rrtype = 'SOA' AND 
        proto = 'udp'
    GROUP BY time(1m), dst_name, af fill(0)
END
```


## "dnsprobe"."rp_mes_dnsprobe"."mes_dnsprobe"

|KeyType |name               |SOA measurement    | DNSKEY measurement | NS measurement   |
| ----   | ----              | ----              | ----               | ----             |
|tagKey  |af                 |    Y              |     Y              |    Y             |
|tagKey  |dst_addr           |    Y              |     Y              |    Y             |
|tagKey  |dst_name           |    Y              |     Y              |    Y             |
|tagKey  |error_class_name   |    Y              |     Y              |    Y             |
|tagKey  |got_response       |    Y              |     Y              |    Y             |
|tagKey  |slr_exceeded       |    Y              |     Y              |    Y             |
|tagKey  |nsid               |    Y              |     Y              |    Y             |
|tagKey  |prb_id             |    Y              |     Y              |    Y             |
|tagKey  |prb_lat            |    Y              |     Y              |    Y             |
|tagKey  |prb_lon            |    Y              |     Y              |    Y             |
|tagKey  |proto              |    Y              |     Y              |    Y             |
|tagKey  |qname              |    Y              |     Y              |    Y             |
|tagKey  |rrtype             |    Y              |     Y              |    Y             |
|tagKey  |src_addr           |    Y              |     Y              |    Y             |
|fieldkey|got_response_field |    Y              |     Y              |    Y             |
|fieldkey|slr_exceeded_field |    Y              |     Y              |    Y             |
|fieldkey|data               |    N              |(success:?,fail:N)  |(success:Y,fail:N)|
|fieldkey|id                 |(success:Y,fail:N) |(success:Y,fail:N)  |(success:Y,fail:N)|
|fieldkey|mname              |(success:Y,fail:N) |(success:N,fail:N)  |(success:N,fail:N)|
|fieldkey|name               |(success:Y,fail:N) |(success:Y,fail:N)  |(success:Y,fail:N)|
|fieldkey|probe_asn          |    Y              |     Y              |    Y             |
|fieldkey|probe_asn_desc     |    Y              |     Y              |    Y             |
|fieldkey|probe_uptime       |    Y              |     Y              |    Y             |
|fieldkey|reason             |(success:N,fail:Y) |(success:N,fail:Y)  |(success:N,fail:Y)|
|fieldkey|rname              |(success:Y,fail:N) |(success:N,fail:N)  |(success:N,fail:N)|
|fieldkey|serial             |(success:Y,fail:N) |(success:N,fail:N)  |(success:N,fail:N)|
|fieldkey|time_took          |    Y              |    Y               |    Y             |
|fieldkey|ttl                |(success:Y,fail:N) |(success:Y,fail:N)  |(success:Y,fail:N)|
|fieldkey|type               |(success:Y,fail:N) |(success:Y,fail:N)  |(success:Y,fail:N)|

?: depend on configuration
